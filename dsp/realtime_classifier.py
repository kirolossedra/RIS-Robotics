from __future__ import annotations

from pathlib import Path
from typing import List, Mapping, Optional, Tuple, Union

import numpy as np


CLASS_NAMES = {
    0: "Sitting on Toilet",
    1: "Standing up from Toilet",
    2: "Washing Hands",
    3: "Fallen",
    4: "Walking",
    6: "Cleaning",
}


# Output order for a future model trained on the new application.
DETECTION_CLASS_NAMES = {
    0: "Person detected",
    1: "Robot detected",
    2: "Nothing detected",
}

# Temporary wiring for the existing seven-output activity model only. These
# assignments have NO person/robot/empty-scene meaning and are for UI testing.
# Replace this mapping and the model together once a detector is trained.
PLACEHOLDER_CLASS_NAMES = {
    0: DETECTION_CLASS_NAMES[0],
    1: DETECTION_CLASS_NAMES[1],
    2: DETECTION_CLASS_NAMES[2],
    3: DETECTION_CLASS_NAMES[2],
    4: DETECTION_CLASS_NAMES[2],
    5: DETECTION_CLASS_NAMES[2],
    6: DETECTION_CLASS_NAMES[2],
}


class RealtimeRadarClassifier:
    """Convert raw SDK frames into ElephasCare maps and run the CNN-LSTM."""

    def __init__(
        self,
        model_path: Union[str, Path],
        num_rx: int,
        num_chirps: int,
        num_samples: int,
        window_frames: int = 10,
        target_shape: Tuple[int, int] = (32, 256),
        class_names: Optional[Mapping[int, str]] = None,
    ) -> None:
        if num_rx < 3:
            raise ValueError("Realtime classification needs at least 3 RX antennas.")
        if window_frames < 1:
            raise ValueError("window_frames must be positive.")

        import keras

        self.model = keras.saving.load_model(model_path, compile=False)
        self.class_names = dict(CLASS_NAMES if class_names is None else class_names)
        if class_names is not None:
            output_count = self.model.output_shape[-1]
            if set(self.class_names) != set(range(output_count)):
                raise ValueError("class_names must label every model output index exactly once.")
        self.num_chirps = num_chirps
        self.num_samples = num_samples
        self.num_rx = 3
        self.window_frames = window_frames
        self.target_shape = target_shape

        self.range_window = blackman_harris(num_samples).reshape(1, num_samples)
        self.doppler_window = blackman_harris(num_chirps).reshape(1, num_chirps)
        self.dopp_avg = np.zeros((num_samples // 2, num_chirps * 2, self.num_rx), dtype=complex)

        angle_len = num_chirps * 2
        self.theta_vec = np.linspace(-np.pi / 2, np.pi / 2, angle_len)
        self.phi_vec = np.linspace(-np.pi / 2, np.pi / 2, angle_len)
        self.a_theta = np.exp(-1j * np.pi * np.sin(self.theta_vec))
        self.a_phi = np.exp(-1j * np.pi * np.sin(self.phi_vec))

        self.azimuth_segment: List[np.ndarray] = []
        self.elevation_segment: List[np.ndarray] = []
        self.doppler_segment: List[np.ndarray] = []

    def warm_up(self) -> None:
        """Initialize model inference before acquisition starts, without buffering frames."""
        shape = (self.window_frames, *self.target_shape)
        self._predict([np.zeros(shape, dtype=np.float32) for _ in range(2)])

    def process_frame(self, frame_data: np.ndarray) -> Optional[Tuple[str, float, np.ndarray]]:
        """Return a prediction every window_frames; otherwise return None."""
        #azimuth, elevation, doppler = self._make_maps(frame_data)
        elevation, doppler = self._make_maps(frame_data)

        #self.azimuth_segment.append(azimuth)
        self.elevation_segment.append(elevation)
        self.doppler_segment.append(doppler)

        if len(self.elevation_segment) < self.window_frames:
            return None

        input_maps = [
            #np.stack(self.azimuth_segment[-self.window_frames:]),
            np.stack(self.elevation_segment[-self.window_frames:]),
            np.stack(self.doppler_segment[-self.window_frames:]),
        ]

        #self.azimuth_segment.clear()
        self.elevation_segment.clear()
        self.doppler_segment.clear()

        return self._predict(input_maps)

    def _make_maps(self, frame_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        range_dopp_prof = []
        doppler_map = np.zeros((self.num_samples // 2, self.num_chirps * 2), dtype=complex)

        for ant_idx in range(self.num_rx):
            mat = frame_data[ant_idx, :, :]
            mat = mat - np.average(mat, axis=1).reshape(self.num_chirps, 1)
            mat = np.multiply(mat, self.range_window)

            zp1 = np.pad(mat, ((0, 0), (0, self.num_samples)), "constant")
            range_fft = np.fft.fft(zp1) / self.num_samples
            range_fft = 2 * range_fft[:, range(self.num_samples // 2)]

            fft1d = np.transpose(range_fft)
            fft1d = np.multiply(fft1d, self.doppler_window)

            zp2 = np.pad(fft1d, ((0, 0), (0, self.num_chirps)), "constant")
            fft2d = np.fft.fft(zp2) / self.num_chirps

            self.dopp_avg[:, :, ant_idx] = (fft2d * 0.6) + (self.dopp_avg[:, :, ant_idx] * 0.4)
            fft2d_mti = fft2d - self.dopp_avg[:, :, ant_idx]
            doppler_fft = np.fft.fftshift(fft2d_mti, axes=(1,))

            range_dopp_prof.append(doppler_fft)
            doppler_map = doppler_map + doppler_fft

        range_dopp_prof = np.asarray(range_dopp_prof)
        #azimuth_map = self._capon_map(range_dopp_prof[[0, 2]], self.a_theta)
        elevation_map = self._capon_map(range_dopp_prof[[1, 2]], self.a_phi)

        return (
            #self._prepare_map(azimuth_map),
            self._prepare_map(elevation_map),
            self._prepare_map(doppler_map),
        )

    def _capon_map(self, profiles: np.ndarray, steering_vector: np.ndarray) -> np.ndarray:
        profiles = np.moveaxis(profiles, 0, -1)
        hermitian = (1 / self.num_chirps) * np.conjugate(profiles.transpose([0, 2, 1]))
        inv_covariance = np.linalg.pinv(hermitian @ profiles)
        steering = np.column_stack((np.ones_like(steering_vector), steering_vector))
        denominator = np.einsum(
            "ai,rij,aj->ra", steering.conjugate(), inv_covariance, steering
        )
        return np.divide(
            1, denominator, out=np.zeros_like(denominator), where=denominator != 0
        )

    def _prepare_map(self, data: np.ndarray) -> np.ndarray:
        data = np.abs(data).astype(np.float32)
        if data.shape == self.target_shape:
            return data
        return self._resize_nearest(data, self.target_shape)

    @staticmethod
    def _resize_nearest(data: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        row_idx = np.linspace(0, data.shape[0] - 1, target_shape[0]).round().astype(int)
        col_idx = np.linspace(0, data.shape[1] - 1, target_shape[1]).round().astype(int)
        return data[np.ix_(row_idx, col_idx)]

    def _predict(self, input_maps: List[np.ndarray]) -> Tuple[str, float, np.ndarray]:
        model_inputs = []
        for data in input_maps:
            data = self._normalize_timesteps(data)
            data = np.expand_dims(data, axis=-1)
            data = np.expand_dims(data, axis=0)
            model_inputs.append(data)

        probabilities = self.model.predict(model_inputs, verbose=0)[0]
        class_idx = int(np.argmax(probabilities))
        class_name = self.class_names.get(class_idx, f"Unknown class: {class_idx}")
        return class_name, float(probabilities[class_idx]), probabilities

    @staticmethod
    def _normalize_timesteps(data: np.ndarray) -> np.ndarray:
        mean = np.mean(data, axis=(1, 2), keepdims=True)
        std = np.std(data, axis=(1, 2), keepdims=True)
        return (data - mean) / np.where(std > 0, std, 1e-8)


def blackman_harris(length: int) -> np.ndarray:
    idx = np.arange(length)
    denominator = max(length - 1, 1)
    return (
        0.35875
        - 0.48829 * np.cos((2 * np.pi * idx) / denominator)
        + 0.14128 * np.cos((4 * np.pi * idx) / denominator)
        - 0.01168 * np.cos((6 * np.pi * idx) / denominator)
    )
