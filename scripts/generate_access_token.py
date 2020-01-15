from argparse import ArgumentParser

from IPython.lib import passwd


parser = ArgumentParser('Generate access token for Jupyter Notebook')
parser.add_argument("password", help="The password you want to use for authentication.")

if __name__ == "__main__":
    args = parser.parse_args()

    sha = passwd(args.password)
    print("ACCESS_TOKEN=" + sha)
