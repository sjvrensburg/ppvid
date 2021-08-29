# PPVID: Post Processing Video Lectures

PPVID is a collection of command line tools for processing recorded video lectures. These tools

- speed up the silent parts of a video,
- master the audio of a video to match that of a reference file and
- converts a video to a format suitable for web.

Though I believe that these tools may prove useful to others, they were developed to match my personal workflow.

## Installation

The recommended method of installation is via [pipx](https://pypa.github.io/pipx/):

```bash
pipx install git+https://github.com/sjvrensburg/ppvid
```

## Short Description of Tools

### `speed_up`

The command `speed_up` provides a slimmed down front-end to the [unsilence](https://github.com/lagmoellertim/unsilence) package.

### `master_video`

The command `master_video` uses the [matchering](https://github.com/sergree/matchering) package to process your video's audio to have the same RMS, FR, peak amplitude and stereo width as the reference track.

### `convert4lecture`

Re-encodes a video for distribution to students via online learning platforms (e.g., Moodle). Settings are subjective, but appear to work well when videos consist primarily of slides+audio.

## Usage

Take the video file `in.mkv` and create the video `out.mkv` where the silent parts playback 250% faster. Define silent sections as sections where the volume is lower than -37.5 dB and longer than 0.75 seconds in duration. Note that this also works with other video formats.

```bash
speed_up -s 2.5 -v -37.5 -d 0.75 in.mkv out.mkv
```

Process the audio of `in.mkv` to have the same RMS, FR, peak amplitude and stereo width as the reference audio file `reference.wav`. Will produce a video `in_mastered.mkv`. Note that this also works with other video formats. It is, however, required that the reference audio is a wave file.

```bash
master_video in.mkv reference.wav
```

Convert `in.mkv` to an MP4 file that is suitable for viewing in most browsers. Set the CRF to 28 and use `ffmpeg`'s `slow` preset. This produces a file named `in_converted.mp4`.

```bash
convert4lecture -c 28 -p "slow" in.mkv
```

## FAQ

### Why should I use this if `unsilence`, `matchering` and `ffmpeg` can already do all of this?

You're right, you can and you should. As already stated, PPVID merely provides a frontend to the tools. The options and terminology used here suits my personal needs.

### Does it work on Windows?

In theory, if `ffmpeg` is in your `PATH` then it should work. However, I have not tested this.

### How are you using this?

With COVID, I've been working from home and recording lectures there. My lectures are simply me reading my slides and demonstrating the use of software. I speak quite slowly with a lot of pauses. Removing these pauses in post-production is a pain, hence the `speed_up`.

Typically, after recording in [OBS](https://obsproject.com/), I listen to my recording at 2x speed. I make notes about errors or sections that I need to cut out, ignoring the previously mentioned pauses. I use [shotcut](https://www.shotcut.org/) to quickly remove those errors. Thereafter, I apply `speed_up`.

I use `master_video` to ensure that the sound of my lectures are consistent from one video to the next. This is necessary since the placement of my microphone, tone of my voice, etc. changes between recordings.

Finally, `speed_up` and `master_video` should be applied to high-quality videos prior to any aggressive compression. However, due to file size limits and out of consideration for our students, compression is necessary. Therefore, as a final step, I run `convert4lecture`.

## Acknowledgements

These tools would not exist without the following packages:

- [unsilence](https://github.com/lagmoellertim/unsilence),
- [matchering](https://github.com/sergree/matchering) and
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python).

Many thanks to the developers of those packages.
