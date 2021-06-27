import winsound


def make_sounds(freqs=None, durations=None):
    if freqs is None:
        freqs = [262, 349]
    if durations is None:
        durations = [500, 1000]
    for freq, duration in zip(freqs, durations):
        winsound.Beep(freq, duration)


if __name__ == '__main__':
    make_sounds([300], [700])
