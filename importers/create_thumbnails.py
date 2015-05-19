import os
import PIL
from PIL import Image
import traceback, sys

def main():
    """
        Main function.
    """

    current_directory = os.getcwd()

    # make a thumbnails folder
    thumbnails_directory = os.path.join(current_directory, "thumbnails")
    if not os.path.exists(thumbnails_directory):
        os.makedirs(thumbnails_directory)

    files = [f for f in os.listdir(current_directory) if os.path.isfile(f)]
    for f in files:
        try:
            # loop through the images and convert them
            im = PIL.Image.open(f)
            im.thumbnail([136,102], PIL.Image.ANTIALIAS)
            outfile = os.path.join(thumbnails_directory, os.path.basename(f))
            im.save(outfile, "JPEG")
        except IOError:
            traceback.print_exc(file=sys.stdout)
            print os.path.basename(f), " doesn't look like an image."

    print "Finished"

if __name__ == "__main__":
    main()