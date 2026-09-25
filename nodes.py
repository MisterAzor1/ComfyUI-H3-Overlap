import torch


def _pad_last(images, target):
    missing = target - images.shape[0]
    if missing <= 0:
        return images[:target]
    return torch.cat((images, images[-1:].repeat(missing, 1, 1, 1)), dim=0)


class H3OverlapPrepare:
    """Turn consecutive VHS batches into overlapping, fixed-length H3 windows."""

    def __init__(self):
        self.previous_tail = None
        self.consumed = 0
        self.source_total = None
        self.spatial_shape = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "loaded_frame_count": ("INT", {"forceInput": True}),
                "source_frame_count": ("INT", {"forceInput": True}),
                "window_size": ("INT", {"default": 90, "min": 5, "max": 4096}),
                "overlap": ("INT", {"default": 8, "min": 1, "max": 256}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("h3_window", "real_new_frames", "is_last_batch", "is_first_batch")
    FUNCTION = "prepare"
    CATEGORY = "H3 Overlap"

    def prepare(self, images, loaded_frame_count, source_frame_count, window_size=90, overlap=8):
        loaded = min(int(loaded_frame_count), int(images.shape[0]))
        total = int(source_frame_count)
        overlap = min(int(overlap), int(window_size) - 1)

        current_shape = tuple(images.shape[1:])
        shape_changed = self.spatial_shape is not None and self.spatial_shape != current_shape
        if self.source_total != total or self.consumed >= total or shape_changed:
            self.previous_tail = None
            self.consumed = 0
            self.source_total = total
            self.spatial_shape = current_shape

        current = images[:loaded]
        first = self.previous_tail is None
        if first:
            window = current
        else:
            window = torch.cat((self.previous_tail, current), dim=0)

        window = _pad_last(window, int(window_size))
        self.previous_tail = current[-overlap:].clone() if loaded else self.previous_tail
        self.consumed += loaded
        is_last = self.consumed >= total
        if is_last:
            # The next execution is a fresh run even if the same file and size are reused.
            self.consumed = total
        return (window, loaded, is_last, first)


class H3OverlapStitch:
    """Crossfade duplicate generated boundary frames without changing duration."""

    def __init__(self):
        self.held_tail = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "real_new_frames": ("INT", {"forceInput": True}),
                "is_last_batch": ("BOOLEAN", {"forceInput": True}),
                "is_first_batch": ("BOOLEAN", {"forceInput": True}),
                "overlap": ("INT", {"default": 8, "min": 1, "max": 256}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("stitched_frames",)
    FUNCTION = "stitch"
    CATEGORY = "H3 Overlap"

    def stitch(self, images, real_new_frames, is_last_batch, is_first_batch, overlap=8):
        count = max(0, int(real_new_frames))
        overlap = int(overlap)
        last = bool(is_last_batch)

        if bool(is_first_batch):
            self.held_tail = None

        # Never blend cached frames from an interrupted run or a different resolution.
        if self.held_tail is not None and tuple(self.held_tail.shape[1:]) != tuple(images.shape[1:]):
            self.held_tail = None

        if self.held_tail is None:
            real = images[:count]
            if last or count <= overlap:
                self.held_tail = None
                return (real,)
            emitted = real[:-overlap]
            self.held_tail = real[-overlap:].clone()
            return (emitted,)

        available_overlap = min(overlap, self.held_tail.shape[0], images.shape[0])
        old = self.held_tail[-available_overlap:]
        new = images[:available_overlap]
        weights = torch.linspace(
            0.0, 1.0, available_overlap + 2,
            device=images.device, dtype=images.dtype
        )[1:-1].view(-1, 1, 1, 1)
        blended = old * (1.0 - weights) + new * weights

        new_real = images[overlap:overlap + count]
        if last or new_real.shape[0] <= overlap:
            output = torch.cat((blended, new_real), dim=0)
            self.held_tail = None
            return (output,)

        output = torch.cat((blended, new_real[:-overlap]), dim=0)
        self.held_tail = new_real[-overlap:].clone()
        return (output,)


NODE_CLASS_MAPPINGS = {
    "H3OverlapPrepare": H3OverlapPrepare,
    "H3OverlapStitch": H3OverlapStitch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "H3OverlapPrepare": "H3 Overlap Prepare",
    "H3OverlapStitch": "H3 Overlap Stitch",
}
