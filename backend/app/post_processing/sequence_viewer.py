import open3d as o3d
from open3d import core as o3c
from open3d.visualization import gui
from open3d.visualization import rendering

from time import sleep

from torch.utils import dlpack
import cv2


class SequenceViewer:
    def __init__(self, dataloader) -> None:
        self._loader = dataloader
        self._depth_width = self._loader.depth_width
        self._depth_height = self._loader.depth_height
        self._color_width = min(self._loader.pv_width, self._loader.depth_width)
        self._color_height = int(
            self._color_width * self._loader.pv_height / self._loader.pv_width
        )
        # self._color_height = min(self._loader.pv_height, self._loader.depth_height)
        # self._color_width = int(
        #     self._color_height * self._loader.pv_width / self._loader.pv_height
        # )
        self._num_frames = self._loader.num_frames

    def run(self):
        # control flags
        self._is_paused = False
        self._is_done = False

        # rendering options
        self._bg_color = (0.1, 0.1, 0.1, 1.0)
        self._show_axes = False
        self._show_skybox = False
        self._enable_lighting = False
        self._update_flags = rendering.Scene.UPDATE_POINTS_FLAG

        # materials
        self._mat_pcd = rendering.MaterialRecord()
        self._mat_pcd.shader = "defaultUnlit"
        self._mat_pcd.point_size = 1

        # geometry
        self._pcd = o3d.t.geometry.PointCloud()
        self._pcd.point.positions = o3c.Tensor.zeros(
            (self._depth_width * self._depth_height, 3), dtype=o3c.float32
        )
        self._pcd.point.colors = o3c.Tensor.full(
            (self._depth_width * self._depth_height, 3), 0.9, dtype=o3c.float32
        )
        self._color_img = o3d.t.geometry.Image(
            o3c.Tensor.zeros(
                (self._color_height, self._color_width, 3), dtype=o3c.float32
            )
        )
        self._depth_img = o3d.t.geometry.Image(
            o3c.Tensor.zeros(
                (self._depth_height, self._depth_width, 3), dtype=o3c.float32
            )
        )

        self._app = gui.Application.instance
        self._app.initialize()
        self._window = self._create_window()

        # add callbacks
        self._window.set_on_layout(self._on_layout)
        self._window.set_on_close(self._on_close)
        self._window.set_on_key(self._on_key)

        # add dummy geometry
        self._widget3d.scene.add_geometry("pcd", self._pcd, self._mat_pcd)

        # setup camera
        self._update_camera()

        # print help info
        self._print_help_info()

        # run
        self._app.run_in_thread(self.update)
        self._app.run()

    def _create_window(self, width=800, height=600):
        window = self._app.create_window("Open3D Sequence Viewer", width, height)
        self._width = width * window.scaling
        self._height = height * window.scaling

        # initialize 3D widget
        self._widget3d = gui.SceneWidget()
        self._widget3d.scene = rendering.Open3DScene(window.renderer)
        self._widget3d.scene.set_background(self._bg_color)
        self._widget3d.scene.show_axes(self._show_axes)
        self._widget3d.scene.show_skybox(self._show_skybox)
        self._widget3d.scene.scene.enable_sun_light(self._enable_lighting)
        view = self._widget3d.scene.view
        view.set_post_processing(False)
        window.add_child(self._widget3d)

        # Options panel
        em = window.theme.font_size
        margin = 0.25 * em
        self._panel = gui.Vert(margin, gui.Margins(margin, margin, margin, margin))

        self._widgetColor = gui.ImageWidget(
            o3d.t.geometry.Image(
                o3c.Tensor.zeros(
                    (self._color_height, self._color_width, 3), dtype=o3c.uint8
                )
            )
        )
        self._panel.add_child(gui.Label("PV Image"))
        self._panel.add_child(self._widgetColor)

        self._widgetDepth = gui.ImageWidget(
            o3d.t.geometry.Image(
                o3c.Tensor.zeros(
                    (self._depth_height, self._depth_width, 3), dtype=o3c.uint8
                )
            )
        )
        self._panel.add_child(gui.Label("Depth Image (normalized)"))
        self._panel.add_child(self._widgetDepth)

        window.add_child(self._panel)

        return window

    def _on_layout(self, ctx):
        r = self._window.content_rect
        pref = self._panel.calc_preferred_size(ctx, gui.Widget.Constraints())
        panel_width = pref.width
        panel_height = pref.height
        height = panel_height if r.height < panel_height else r.height
        width = (
            (panel_height + panel_width)
            if r.width < (panel_height + panel_width)
            else r.width
        )
        self._widget3d.frame = gui.Rect(0, 0, width - panel_width, height)
        self._panel.frame = gui.Rect(
            self._widget3d.frame.get_right(), 0, panel_width, height
        )
        self._window.size = gui.Size(width, height)

    def _on_close(self):
        self._is_done = True
        sleep(0.10)
        return True

    def _on_key(self, event):
        if event.key == gui.KeyName.Q:  # quit
            if event.type == gui.KeyEvent.DOWN:
                self._window.close()
                return True

        if event.key == gui.KeyName.SPACE:  # pause
            if event.type == gui.KeyEvent.DOWN:
                self._is_paused = not self._is_paused
                return True

        if event.key == gui.KeyName.R:  # reset camera
            if event.type == gui.KeyEvent.DOWN:
                self._update_camera()
                return True

        if event.key == gui.KeyName.H:  # help
            if event.type == gui.KeyEvent.DOWN:
                self._print_help_info()
                return True

        return False

    def _print_help_info(self):
        print("=" * 60)
        print("Keyboard commands:")
        print("-" * 60)
        print("SPACE: pause")
        print("R: reset camera")
        print("Q: quit")
        print("H: print help info")
        print("=" * 60)

    def _update_camera(self):
        fov = 80.0
        aspect_ratio = float(self._window.size.width) / float(self._window.size.height)
        near = 0.001
        far = 1000.0
        fov_type = rendering.Camera.FovType.Horizontal
        self._widget3d.scene.camera.set_projection(
            fov, aspect_ratio, near, far, fov_type
        )
        self._widget3d.scene.camera.look_at(
            (0, 0, 1), (0, 0, -0.5), (0, -1, 0)
        )  # center, eye, up

    def step(self):
        if self._is_paused:
            return
        self._loader.step()

    def update(self):
        def update_pcd():
            self._pcd.point.positions = o3c.Tensor.from_dlpack(
                dlpack.to_dlpack(self._loader.points.cpu())
            )
            self._widget3d.scene.scene.update_geometry(
                "pcd", self._pcd, self._update_flags
            )

        def update_color():
            img = cv2.resize(
                self._loader.color_image.cpu().numpy(),
                (self._color_width, self._color_height),
                interpolation=cv2.INTER_LINEAR,
            )
            self._widgetColor.update_image(o3d.t.geometry.Image(o3c.Tensor(img)))

        def update_depth():
            img = cv2.resize(
                self._loader.depth_colored.cpu().numpy(),
                (self._depth_width, self._depth_height),
                interpolation=cv2.INTER_LINEAR,
            )
            self._widgetDepth.update_image(o3d.t.geometry.Image(o3c.Tensor(img)))

        while not self._is_done:
            sleep(0.08)
            if not self._is_done:
                self.step()
                self._app.post_to_main_thread(self._window, update_color)
                self._app.post_to_main_thread(self._window, update_depth)
                self._app.post_to_main_thread(self._window, update_pcd)
