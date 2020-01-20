from argparse import ArgumentParser

from IPython.lib import passwd


parser = ArgumentParser('Generate access token for Jupyter Notebook')
parser.add_argument("password", help="The password you want to use for authentication.")

if __name__ == "__main__":
    args = parser.parse_args()

    print(passwd(args.password))
