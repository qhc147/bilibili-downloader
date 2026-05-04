import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

from src.ui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
