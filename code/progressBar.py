from datetime import datetime

def progress_bar(progress, total, start_timestamp):
    BLOCK = '█'
    COLOUR_YELLOW = '\033[33m'
    COLOUR_GREEN = '\033[92m'
    COLOUR_CLEAR = '\033[0m'

    percent = 100 * (progress /float(total))
    bar = BLOCK * int(percent) + '-' * (100 - int(percent))

    time_taken = str((datetime.now() - start_timestamp))
    time_taken = time_taken[:time_taken.find('.')+3]

    print(COLOUR_YELLOW + f'\r |{bar}|{percent:.2f}% | {progress}/{total} | {time_taken} ', end='\r')
    if progress == total:
        print(COLOUR_GREEN + f'\r |{bar}|{percent:.2f}% | {progress}/{total} | {time_taken} ', end='\r')
        print('\nJob Complete\n' + COLOUR_CLEAR, end='\r')
    return f' Job Complete {progress}/{total} | {time_taken}'