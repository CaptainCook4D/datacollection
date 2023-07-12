from matplotlib import pyplot as plt
import _init_path
from datacollection.user_app.backend.app.post_processing import SequenceLoader


def show_image(img, title="show_image"):
    ndim = img.ndim
    print("ndim:", ndim)
    if img.ndim == 2:
        plt.imshow(img.cpu().numpy(), cmap="gray")
    else:
        plt.imshow(img.cpu().numpy())
    plt.title(title)
    plt.show()


if __name__ == "__main__":
    rec_id = "12_19"

    loader = SequenceLoader(rec_id=rec_id, device="cuda:0", debug=True)

    print("device_id:\n", loader.device_id)
    print("depth_mode:\n", loader.depth_mode)
    print("pv_width:\n", loader.pv_width)
    print("pv_height:\n", loader.pv_height)
    print("depth_width:\n", loader.depth_width)
    print("depth_height:\n", loader.depth_height)
    print("num_frames:\n", loader.num_frames)
    print("pv_intrinsic:\n", loader.pv_intrinsic)
    print("pv2rig:\n", loader.pv2rig)
    print("depth2rig:\n", loader.depth2rig)
    print("depth_xy1:\n", loader.depth_xy1)
    print("depth_scale:\n", loader.depth_scale)

    loader.step_by_frame_id(100)
    print("frame_id:\n", loader.frame_id)
    points = loader.points
    print("points:\n", points.shape, points.dtype, points.device)
    color_img = loader.color_image
    print("color_img:\n", color_img.shape, color_img.dtype, color_img.device)
    depth_img = loader.depth_image
    print("depth_img:\n", depth_img.shape, depth_img.dtype, depth_img.device)
    depth_colored = loader.depth_colored
    print(
        "depth_coloried:\n",
        depth_colored.shape,
        depth_colored.dtype,
        depth_colored.device,
    )

    show_image(color_img, title="color_img")
    show_image(depth_img, title="depth_img")
    show_image(depth_colored, title="depth_colored")
