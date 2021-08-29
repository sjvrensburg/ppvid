from unsilence import Unsilence
from ppvid.utilities import log_info, log_warning, get_erase_char, repair_console
from rich.console import Console
from rich.progress import Progress
from tempfile import TemporaryDirectory
from os.path import join
from os import getcwd
import soundfile as sf
import pyloudnorm as pyln
import matchering as mg
import ffmpeg
import click
import sys


@click.command()
@click.argument('infile')
@click.argument('outfile')
@click.option(
    '-s', '--speed', default=2.5,
    help='The speed at which the silent intervals get played back at.')
@click.option(
    '-v', '--vthresh', default=-37.5,
    help='Threshold of what should be classified as silent/audible (default -37.5)')
@click.option(
    '-d', '--dthresh', default=0.75,
    help='The shortest allowed interval length (default 0.75 seconds)')
@click.option(
    '-t', '--threads', default=1,
    help='Number of threads to use (default 1)')
def speed_up(
    infile: str,
    outfile: str,
    speed: float = 2.5,
    vthresh: float = -37.5,
    dthresh: float = 0.75,
    threads: int = 1,
    exit: bool=True):
    "Front-end to unsilence, with sane defaults."
        
    if exit:
        erase_char = get_erase_char()
        repair_console(erase_char)

    console = Console()
    progress = Progress()

    u = Unsilence(infile)
    
    with progress:
        def update_task(current_task):
            def handler(current_val, total):
                progress.update(current_task, total=total, completed=current_val)

            return handler

        silence_detect_task = progress.add_task("Calculating Intervals...", total=1)
        u.detect_silence(
            silence_level = vthresh,
            silence_time_threshold = dthresh,
            short_interval_threshold = max(dthresh / speed, 0.5),
            stretch_time = 0.325,
            on_silence_detect_progress_update = update_task(silence_detect_task))
        progress.stop()
        progress.remove_task(silence_detect_task)

        progress.start()
        rendering_task = progress.add_task("Rendering Intervals...", total=1)
        concat_task = progress.add_task("Combining Intervals...", total=1)

        u.render_media(
            outfile,
            on_render_progress_update=update_task(rendering_task),
            on_concat_progress_update=update_task(concat_task),
            silent_speed=speed, silent_volume=0, threads=threads)

        progress.stop()
        progress.remove_task(concat_task)
    
    u.cleanup()

    console.print('DONE!')
    if exit:
        repair_console(erase_char)
        sys.exit(0)


@click.command()
@click.argument('infile')
@click.argument('reference')
def master_video(
    infile: str,
    reference: str,
    exit: bool=True):
    """
    Master using matchering. Matchering tries to master the audio of `infile` such that
    it matches the frequency and loudness of the `reference` file. It produces a new
    video with the audio of `infile` replaced by the mastered audio. The new video's
    file name has the string `_mastered` apprended to it. 
    
    ARGUMENTS
    infile (str):       Name of or path to the video to process.

    reference (str):    Name of or path to the reference audio.
    
    exit (bool):        Should the command exit to the console after it is finished?
                        Option is only available if the function is used from within
                        a script, i.e., if you are running this as a command then
                        you don't have to worry about this argument.
    """

    cwd = getcwd()
    console = Console()
        
    if exit:
        erase_char = get_erase_char()
        repair_console(erase_char)
    
    with TemporaryDirectory() as tmp_dir:
        # Extract the audio of our video
        in_video = ffmpeg.input(infile).video
        in_audio = ffmpeg.input(infile).audio
        console.log("Extracting audio from video.")
        in_audio.output(join(tmp_dir, "in_audio.wav")).run()
        console.log("Preparing Matchering...")
        mg.log(
            warning_handler=lambda x: log_warning(x, console),
            info_handler=lambda x: log_info(x, console))
        console.log("Matchering started...")
        mg.process(
            # The track you want to master
            target=join(tmp_dir, "in_audio.wav"),
            # Some "wet" reference track
            reference=reference,
            # Where and how to save your results
            results=[
                mg.pcm16(join(tmp_dir, "master_16bit.wav")),
                mg.pcm24(join(tmp_dir, "master_24bit.wav")),
            ],
            config=mg.Config(max_length = 120 * 60),)
        console.log("Matchering is done...")
        # Normalise the matchering output
        data, rate = sf.read(join(tmp_dir, "master_24bit.wav"))
        meter = pyln.Meter(rate) # create BS.1770 meter
        peak_normalized_audio = pyln.normalize.peak(data, -1.0)
        loudness = meter.integrated_loudness(peak_normalized_audio)
        loudness_normalized_audio = pyln.normalize.loudness(
            peak_normalized_audio, loudness, -15.0)
        sf.write(
            join(tmp_dir, "master_24bit.wav"),
            loudness_normalized_audio,
            rate)
        out_audio = ffmpeg.input(
            join(tmp_dir, "master_24bit.wav")).audio
        outfile = infile.split('.')
        n = len(outfile)
        extension = outfile[n-1]
        outfile = '{}_mastered.{}'.format('.'.join(outfile[:-1]), extension)
        console.log("About to export {}".format(outfile))
        ffmpeg.output(
            in_video,
            out_audio,
            join(cwd, outfile)).run()

    console.print('DONE!')
    if exit:
        repair_console(erase_char)
        sys.exit(0)


@click.command()
@click.argument('infile')
@click.option(
    '-c', '--crf', default=26,
    help='Constant Rate Factor (CRF): Affects quality, lower is better (default 26)\nNOTE: ffmpeg\'s default is 23.')
@click.option(
    '-p', '--preset', default='veryslow',
    help='ffmpeg preset (default \'veryslow\')')
def convert4lecture(
    infile: str,
    crf: int=26,
    preset: str='veryslow',
    exit: bool=True):
    """
    Convert `infile` to a format that is suitable for use on Moodle. For now, this an `mp4`
    file using the `libx264` video codec and `aac` audio codec. The converted video's
    file name has the string `_converted` apprended to it.
    
    ARGUMENTS
    infile (str):       Name of or path to the video to convert.
    crf (int):          Constant Rate Factor (CRF): Affects quality, lower is better (default 26)
    preset (str):       ffmpeg preset, affects compression.
    exit (bool):        Should the command exit to the console after it is finished?
                        Option is only available if the function is used from within
                        a script, i.e., if you are running this as a command then
                        you don't have to worry about this argument.
    
    NOTE: ffmpeg\'s defaults are `crf=23` and `preset=\'fast\'`. If you find that the quality
    is too low, lower the `crf` value. If encoding is too slow, try changing the preset.
    """
        
    if exit:
        erase_char = get_erase_char()
        repair_console(erase_char)

    cwd = getcwd()
    outfile = infile.split('.')
    outfile = '{}_converted.mp4'.format('.'.join(outfile[:-1]))
    ffmpeg.input(
        infile).output(
            join(cwd, outfile),
            vcodec='libx264',
            crf=crf, preset=preset,
            acodec='aac',
            movflags='faststart').run()

        
    if exit:
        repair_console(erase_char)
        sys.exit(0)
