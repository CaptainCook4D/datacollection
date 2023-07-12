import _init_path
from datacollection.user_app.backend.app.post_processing import (
    SequenceLoader,
    SequenceViewer,
)


if __name__ == "__main__":
    rec_id = "7_5"

    loader = SequenceLoader(rec_id=rec_id, device="cuda:0", debug=False)

    viewer = SequenceViewer(dataloader=loader)
    viewer.run()
