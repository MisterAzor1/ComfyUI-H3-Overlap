# ComfyUI-H3-Overlap

Memory-efficient overlapping frame preparation and seamless crossfade stitching for long MiniMax H3 video workflows in ComfyUI.

The nodes divide long videos into smaller overlapping windows, allowing H3 video passes to run on lower-VRAM systems. Processed windows are then stitched together while preserving the original frame count.

## Features

- Processes long videos in VRAM-friendly sections
- Configurable processing-window size
- Configurable frame overlap
- Crossfades overlapping frames between sections
- Pads incomplete final windows automatically
- Removes padded frames from the finished video
- Preserves the exact original frame count
- Automatically resets cached frames between executions
- Supports portrait, landscape, and square videos
- Does not require additional Python packages

## Included Nodes

### H3 Overlap Prepare

Converts incoming image batches into fixed-size overlapping processing windows.

It:

- Adds frames from the previous section to provide temporal context
- Pads the final section when it is shorter than the required window
- Tracks the number of real frames
- Identifies the first and final processing windows

### H3 Overlap Stitch

Combines the processed windows into one continuous image sequence.

It:

- Crossfades duplicate overlap frames
- Removes temporary padding
- Prevents duplicated boundary frames
- Returns the exact original video length
- Clears stored state when a new execution starts

## Recommended Settings

For a 90-frame H3 processing window:

| Setting | Value |
|---|---:|
| Source frames per batch | 82 |
| Window size | 90 |
| Overlap | 8 |
| Stride | 82 |

The source batch size must equal:

```text
source batch size = window size - overlap
```

For the recommended settings:

```text
82 = 90 - 8
```

If you change the window size or overlap, update the source batch size accordingly.

## Installation

Open your ComfyUI `custom_nodes` directory:

```bash
cd ComfyUI/custom_nodes
```

Clone this repository:

```bash
git clone https://github.com/MisterAzor1/ComfyUI-H3-Overlap.git
```

Restart ComfyUI.

The nodes will appear under:

```text
H3 Overlap
```

## Updating

Open the installed repository directory and pull the latest version:

```bash
cd ComfyUI/custom_nodes/ComfyUI-H3-Overlap
git pull
```

Restart ComfyUI afterward.

## Basic Workflow

Connect the nodes in this order:

```text
Video/Image Batch
        ↓
H3 Overlap Prepare
        ↓
MiniMax H3 Processing
        ↓
H3 Overlap Stitch
        ↓
Video Combine
```

All processing performed between the Prepare and Stitch nodes must preserve:

- Frame order
- Batch order
- Width and height
- The number of frames in each prepared window

Do not resize individual windows to different dimensions.

## Example Workflow

An example workflow is available here:

```text
example_workflows/h3_sharpen_overlap_1mp.json
```

The example demonstrates:

- MiniMax H3 processing
- Sharpness LoRA processing
- 90-frame processing windows
- 8-frame overlap
- 82-frame source batches
- Dynamic output sizing
- Optional MiniMax H3 3D latent upscaling
- Approximately one-megapixel output

## Example Workflow Dependencies

The custom nodes themselves do not require additional Python packages.

The included example workflow may require:

- ComfyUI
- VideoHelperSuite
- KJNodes
- MiniMax H3 custom nodes
- A compatible MiniMax H3 model
- A compatible sharpness LoRA
- Painter MiniMax H3 3D latent upscaler nodes, if enabled

Models, LoRAs, and third-party custom nodes are not included in this repository.

## Resolution Requirements

Every frame in one execution must use the same width and height.

When using a latent upscaler:

- Calculate its dimensions from the resized input
- Preserve the source aspect ratio
- Use dimensions compatible with the selected latent model
- Keep all processing windows at identical dimensions
- Avoid manually entering unrelated width and height values

Changing resolution during an active execution can cause tiled, overlaid, distorted, or incorrectly stitched output.

## Audio

These nodes process image frames only.

They do not divide, cache, crossfade, or stitch audio. Audio should be taken from the original source and muxed into the finished video separately.

If the source video does not contain a valid audio stream, leave the audio input on the video-combine node disconnected.

## Troubleshooting

### Tiled or overlaid output

Possible causes:

- The latent upscaler received an incompatible latent format
- The upscaler dimensions do not match the video aspect ratio
- Different windows were processed at different dimensions
- A latent-processing node changed the expected tensor layout

Verify the workflow without the latent upscaler first. Add the upscaler only after the overlap workflow produces a correct video.

### Crossfade or overlap node fails

Verify that:

```text
source batch size = window size - overlap
```

Also verify that every processed window has the same resolution.

### Visible transition between windows

Increase the overlap slightly or reduce the amount of visual change introduced during processing.

Larger overlaps may improve transitions but require more VRAM and processing time.

### Extra frozen frames at the end

Update to the latest version of the nodes. The final window must report its real-frame count so temporary padding can be removed.

### Missing or duplicated frames

Confirm that the batch size, window size, and overlap follow the required formula.

### Frames from an earlier video appear

Update to the latest version. Current versions automatically reset cached state when a new execution begins or the input resolution changes.

### No audio in the finished video

The overlap nodes do not process audio. Connect the source audio directly to the final video-combine stage or remux it afterward.

## Tested Configuration

Tested with:

- 12 GB VRAM
- ComfyUI 0.34.x
- MiniMax H3 video processing
- 90-frame processing windows
- 8-frame overlap
- 82-frame source batches
- Portrait and landscape video
- Videos up to 643 frames
- Approximately 0.5-megapixel processing resolution
- Optional approximately 1-megapixel final output

Performance depends on the model, resolution, frame count, GPU, attention implementation, and other nodes in the workflow.

## Reporting Problems

When opening an issue, include:

- ComfyUI version
- GPU model
- VRAM amount
- Video resolution
- Original frame count
- Source frames per batch
- Window size
- Overlap size
- Complete console error
- A workflow JSON with personal paths and filenames removed

Do not upload private videos, model files, API keys, or personal filesystem paths.

## Disclaimer

This project is not affiliated with MiniMax, Comfy Org, Painter, VideoHelperSuite, KJNodes, or the creators of any referenced models.

Model licenses and usage restrictions remain applicable.

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.
