import os
from pathlib import Path
import cv2
import matplotlib.pyplot as plt
import numpy as np
import yaml
import pickle
import logging

import torch

from ..hololens import hl2ss, hl2ss_3dcv, hl2ss_utilities

DATA_ROOT = str(Path(__file__).resolve().parents[5] / "data")


class SequenceLoader:
    def __init__(self, rec_id, device="cpu:0", debug=False):
        self._logger = self._init_logger(debug)
        self._rec_id = rec_id
        self._device = device
        # self._data_folder = Path(DATA_ROOT) / "hololens" / rec_id / "sync"
        # self._calib_folder = Path(DATA_ROOT) / "calibration"

        # self._data_folder = Path(f"/data/WEBSITE/{rec_id}") / "sync"
        self._data_folder = Path(f"/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup/PTG/{rec_id}") / "sync"
        self._calib_folder = Path("/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup") / "calibration"

        # load meta data
        self._load_meta_data()

        # load pv calibration data
        self._load_pv_calibration_info()

        # load depth calibration data
        self._load_depth_calibration_info()

        # load calibration data
        self._load_calibration_data()

        # self.spatial_data = self.load_spatial_data()
        # self.pv_pose_data = self.load_pv_pose_data()

        # Get colormap from matplotlib
        self._colormap = plt.get_cmap("jet")

        self._color_files = [
            str(self._data_folder / "pv" / "frames" / f"color-{i:06d}.jpg")
            for i in range(self._num_frames)
        ]
        self._depth_files = [
            str(self._data_folder / "depth_ahat" / "depth" / f"depth-{i:06d}.png")
            for i in range(self._num_frames)
        ]

        self._frame_id = -1
        self._points = None
        self._colors = None
        self._depth_img = np.zeros(
            (self._depth_height, self._depth_width), dtype=np.uint16
        )
        self._color_img = None

    def _init_logger(self, debug):
        logger = logging.getLogger("SequenceLoader")
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG if debug else logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def _load_data_from_pickle_file(self, file_path):
        with open(file_path, "rb") as f:
            data = pickle.load(f)
        return data

    def _load_data_from_bin_file(self, file_path):
        data = np.fromfile(file_path, dtype=np.float32)
        return data

    def _load_data_from_yaml_file(self, file_path):
        with open(file_path, "r") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        return data

    def _load_color_image_as_tensor(self, file_path):
        color = cv2.imread(file_path)
        color = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
        # color = torch.from_numpy(color.astype(np.float32) / 255.0).to(
        #     self._device
        # )  # shape: [H, W, 3]
        color = torch.from_numpy(color)
        return color

    def _load_depth_image_as_tensor(self, file_path):
        depth = cv2.imread(file_path, cv2.IMREAD_ANYDEPTH)
        depth = torch.from_numpy(depth.astype(np.float32)).to(
            self._device
        )  # shape: [H, W]
        return depth

    def _colorize_depth(self, depth, min_depth=0.0, max_depth=2.0):
        # Min-max depth normalization
        depth_scale = depth / self._depth_scale
        depth_scale[depth_scale < min_depth] = 0.0
        depth_scale[depth_scale > max_depth] = 0.0
        depth_norm = (depth_scale - min_depth) / (max_depth - min_depth)
        # Apply colormap
        depth_colored = self._colormap(depth_norm.cpu().numpy())[:, :, :3] * 255
        return torch.from_numpy(depth_colored.astype(np.uint8))

    def _load_meta_data(self):
        self._logger.debug("Loading meta data...")
        meta_file = self._data_folder / "meta.yaml"
        data = self._load_data_from_yaml_file(str(meta_file))
        self._device_id = data["device_id"]
        self._depth_mode = data["depth_mode"]
        self._pv_width = data["pv_width"]
        self._pv_height = data["pv_height"]
        self._depth_width = data["depth_width"]
        self._depth_height = data["depth_height"]
        self._num_frames = data["num_of_frames"]
        self._logger.debug("Meta data loaded.")

    def _load_extrinsic_matrix(self, file_path):
        data = self._load_data_from_bin_file(file_path)
        T = data.reshape(4, 4).transpose()
        return torch.from_numpy(T).to(self._device)

    def _load_intrinsic_matrix(self, file_path):
        data = self._load_data_from_bin_file(file_path)
        K = data.reshape(4, 4).transpose()
        return torch.from_numpy(K[:3, :3]).to(self._device)

    def _load_pv_calibration_info(self):
        pv_calib_folder = self._calib_folder / self._device_id / "personal_video"
        self._pv2rig = self._load_extrinsic_matrix(
            str(pv_calib_folder / "extrinsics.bin")
        )
        self._pv_intrinsic = self._load_intrinsic_matrix(
            str(
                pv_calib_folder
                / f"1000_{self._pv_width}_{self._pv_height}"
                / "intrinsics.bin",
            )
        )

    def _load_depth_calibration_info(self):
        depth_calib_folder = (
            self._calib_folder / self._device_id / f"rm_depth_{self._depth_mode}"
        )
        self._depth2rig = self._load_extrinsic_matrix(
            str(depth_calib_folder / "extrinsics.bin")
        )
        if self._depth_mode == "long":
            self._depth_scale = 1000.0
        elif self._depth_mode == "ahat":
            self._depth_scale = 250.0
        else:
            self._depth_scale = self._depth_scale = self._load_data_from_bin_file(
                str(depth_calib_folder / "scale.bin")
            ).item()
        uv2xy = self._load_data_from_bin_file(
            str(depth_calib_folder / "uv2xy.bin")
        ).reshape((-1, 2))
        xy1 = np.concatenate(
            (uv2xy, np.ones((uv2xy.shape[0], 1), dtype=np.float32)), axis=-1
        )
        self._depth_xy1 = torch.from_numpy(xy1).to(self._device)

    def _load_calibration_data(self):
        pv_calib_folder = self._calib_folder / self._device_id / "personal_video"
        self._principal_point = self._load_data_from_bin_file(
            str(
                pv_calib_folder
                / f"1000_{self._pv_width}_{self._pv_height}"
                / "principal_point.bin"
            )
        )
        self._focal_length = self._load_data_from_bin_file(
            str(
                pv_calib_folder
                / f"1000_{self._pv_width}_{self._pv_height}"
                / "focal_length.bin"
            )
        )
        self._intrinsics = torch.tensor(
            [
                [-self._focal_length[0], 0, self._principal_point[0]],
                [0, self._focal_length[1], self._principal_point[1]],
                [0, 0, 1],
            ],
            dtype=torch.float32,
            device=self._device,
        )

    def _deproject(self, depth, scale=1000.0, depth_min=0.1, depth_max=2.0):
        # process depth image
        depth = depth / scale
        depth[depth < depth_min] = 0.0
        depth[depth > depth_max] = 0.0
        # Reshape and repeat depth values
        depth = depth.view(-1, 1).repeat(1, 3)
        # Compute 3D points
        points = depth * self._depth_xy1
        return points

    def cam2world(self, points, cam2world_matrix):
        homog_points = np.hstack((points, np.ones((points.shape[0], 1))))
        world_points = np.matmul(cam2world_matrix, homog_points.T)
        return world_points.T[:, :3], cam2world_matrix

    def load_spatial_data(self):
        spatial_data_folder = self._data_folder / "spatial"
        spatial_data = self._load_data_from_pickle_file(
            str(spatial_data_folder / f"{self.rec_id}_spatial.pkl")
        )
        spatial_data = list(spatial_data.values())
        print(len(spatial_data))
        return spatial_data

    def load_pv_pose_data(self):
        pv_pose_data = self._load_data_from_pickle_file(
            str(self._data_folder / "pv" / f"{self.rec_id}_pv_pose.pkl")
        )
        pv_pose_data = list(pv_pose_data.values())
        print(len(pv_pose_data))
        return pv_pose_data

    @classmethod
    def project_points(cls, image, P, points, radius, color, thickness):
        for x, y in hl2ss_3dcv.project(points, P):
            cv2.circle(image, (int(x), (int(y))), radius, color, thickness)

    def project_spatial(self, image, pv_pose, data_si: hl2ss.unpack_si):
        # Marker properties
        radius = 5
        color = (0, 255, 255)
        thickness = 3

        if hl2ss.is_valid_pose(pv_pose) and (data_si is not None):
            projection = hl2ss_3dcv.world_to_reference(
                pv_pose
            ) @ hl2ss_3dcv.camera_to_image(self._intrinsics)
            si = data_si
            if si.is_valid_hand_left():
                self.project_points(
                    image,
                    projection,
                    hl2ss_utilities.si_unpack_hand(si.get_hand_left()).positions,
                    radius,
                    color,
                    thickness,
                )
            if si.is_valid_hand_right():
                self.project_points(
                    image,
                    projection,
                    hl2ss_utilities.si_unpack_hand(si.get_hand_right()).positions,
                    radius,
                    color,
                    thickness,
                )

    def step(self):
        self._frame_id = (self._frame_id + 1) % self._num_frames
        self.step_by_frame_id(self._frame_id)

    def step_by_frame_id(self, frame_id):
        self._frame_id = frame_id % self._num_frames
        self._depth_img = self._load_depth_image_as_tensor(
            self._depth_files[self._frame_id]
        )
        self._depth_colored = self._colorize_depth(self._depth_img)
        self._color_img = self._load_color_image_as_tensor(
            self._color_files[self._frame_id]
        )
        self._points = self._deproject(self._depth_img, self._depth_scale)
        # self._color_pose = self.pv_pose_data[self._frame_id][0]
        # self._spatial = self.spatial_data[self._frame_id][0]
        # self.project_spatial(self._color_img, self._color_pose, self._spatial)

    @property
    def rec_id(self):
        return self._rec_id

    @property
    def device(self):
        return self._device

    @property
    def data_folder(self):
        return str(self._data_folder)

    @property
    def device_id(self):
        return self._device_id

    @property
    def depth_mode(self):
        return self._depth_mode

    @property
    def pv_width(self):
        return self._pv_width

    @property
    def pv_height(self):
        return self._pv_height

    @property
    def depth_width(self):
        return self._depth_width

    @property
    def depth_height(self):
        return self._depth_height

    @property
    def num_frames(self):
        return self._num_frames

    @property
    def pv2rig(self):
        return self._pv2rig

    @property
    def pv_intrinsic(self):
        return self._pv_intrinsic

    @property
    def depth2rig(self):
        return self._depth2rig

    @property
    def depth_xy1(self):
        return self._depth_xy1

    @property
    def depth_scale(self):
        return self._depth_scale

    @property
    def frame_id(self):
        return self._frame_id

    @property
    def points(self):
        return self._points

    @property
    def depth_image(self):
        return self._depth_img

    @property
    def depth_colored(self):
        return self._depth_colored

    @property
    def color_image(self):
        return self._color_img
