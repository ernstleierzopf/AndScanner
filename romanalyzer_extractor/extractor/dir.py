from pathlib import Path


class DirExtractor(object):

    def __init__(self, target, target_path=None):
        self.target = Path(target)
    
    def extract(self):
        paths = []
        if self.target.exists() and self.target.is_dir():
            paths = [file for file in self.target.rglob('*') if not file.is_dir()]
            # for path in paths:
            #     if path.name.lower() == "super.img" or path.name.lower().endswith("sparsechunk.0"):
            #         # add super.img to the end of the list.
            #         paths.remove(path)
            #         paths.append(path)
        return paths
