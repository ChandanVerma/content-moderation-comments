import os
import boto3
import logging

logger = logging.getLogger("ray")
logger.setLevel("INFO")


def download_models_helper(root="./models"):
    """Download model files from S3.

    Args:
        root (str, optional): Folder directory where model files will be stored.\
        Defaults to "./models".
    """

    logger.info(
        "Env vars within download models helper are: {}, {}, {}".format(
            os.environ.get("AWS_ROLE_ARN"),
            os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE"),
            os.environ.get("AWS_DEFAULT_REGION"),
        )
    )
    logger.info(
        "Model files will be saved in: {}".format(os.path.join(os.getcwd(), "models"))
    )
    s3 = boto3.client("s3")

    if not os.path.exists(root):
        os.makedirs(root)
    if not os.path.exists(os.path.join(root, "checkpoints")):
        os.makedirs(os.path.join(root, "checkpoints"))
    if not os.path.exists(
        os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en")
    ):
        os.makedirs(os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en"))
    if not os.path.exists(
        os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en", "blobs")
    ):
        os.makedirs(
            os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en", "blobs")
        )
    if not os.path.exists(
        os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en", "refs")
    ):
        os.makedirs(
            os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en", "refs")
        )
    if not os.path.exists(
        os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en", "snapshots")
    ):
        os.makedirs(
            os.path.join(root, "models--Helsinki-NLP--opus-mt-ROMANCE-en", "snapshots")
        )
    if not os.path.exists(
        os.path.join(
            root,
            "models--Helsinki-NLP--opus-mt-ROMANCE-en",
            "snapshots",
            "5337de927e4fef5c133c7d11350733c93a73159a",
        )
    ):
        os.makedirs(
            os.path.join(
                root,
                "models--Helsinki-NLP--opus-mt-ROMANCE-en",
                "snapshots",
                "5337de927e4fef5c133c7d11350733c93a73159a",
            )
        )

    files = [
        "checkpoints/multilingual_debiased-0b549669.ckpt",
        "checkpoints/toxic_original-c1212f89.ckpt",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/blobs/9d77bbbd43a214959e027ffc8713fbe31f8609d14827fba645f1361ca20a6f3a",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/blobs/87cd76224ab570a3aadf39215a6344011b170e4e",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/blobs/9080d95ae1341be221ff48919ea4a362970ac9a0",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/blobs/090397efd72233e61e84abe704ff4d3146f451db",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/blobs/d53a30938309af55bb3dc44e59034a3acfd620ba",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/blobs/da7a7e613f68cd0373521753d65267e3ae6c345f",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/refs/main",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/snapshots/5337de927e4fef5c133c7d11350733c93a73159a/config.json",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/snapshots/5337de927e4fef5c133c7d11350733c93a73159a/pytorch_model.bin",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/snapshots/5337de927e4fef5c133c7d11350733c93a73159a/source.spm",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/snapshots/5337de927e4fef5c133c7d11350733c93a73159a/target.spm",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/snapshots/5337de927e4fef5c133c7d11350733c93a73159a/tokenizer_config.json",
        "models--Helsinki-NLP--opus-mt-ROMANCE-en/snapshots/5337de927e4fef5c133c7d11350733c93a73159a/vocab.json",
        "280541649472174b9a8bfa31ba0c861e806be14d2f60113b6da0d1fb5ec395bb.c7a1c260ba157336a16a3228f89a319e62669fcbb609e915f81ad0a41cde9a36.json",
        "280541649472174b9a8bfa31ba0c861e806be14d2f60113b6da0d1fb5ec395bb.c7a1c260ba157336a16a3228f89a319e62669fcbb609e915f81ad0a41cde9a36.lock",
        "dbe77a7e08998d5dd16d296d52ac847d948ce8623f9d03521523228adef7738a.f5d5ee4d8c7ca816f3fabd88ce4c54472271b2910a3f09caf4b889aca978f38c.lock",
        "c82b120b36d8b28738f1a1c0757b7f4872c909ec18453800e48e76412b2a224f.d6d474c4ca928339db0d7a9e8e4663b795225c29b46463593ab08c445ad08fbf",
        "dbe77a7e08998d5dd16d296d52ac847d948ce8623f9d03521523228adef7738a.f5d5ee4d8c7ca816f3fabd88ce4c54472271b2910a3f09caf4b889aca978f38c",
        "eeea462f521dc2d50bc28be24a8993a6f84552c3b0cc16036733b25b00b76eff.b9af6e61147590608619b5508e4a608e12d5907e641fa73ebb9da3ea5f8c1d94.lock",
        "c82b120b36d8b28738f1a1c0757b7f4872c909ec18453800e48e76412b2a224f.d6d474c4ca928339db0d7a9e8e4663b795225c29b46463593ab08c445ad08fbf.lock",
        "fb5a688525d6c40a1f822784bba5c568a6209a7f68bbfd81ad30aee8af9fe757.2bd248ef954b136f33ba3b5f29736fc22fe21299b45a94ae1edd3136a6f1ddb2",
        "231dc7d689812283cb707214f58bffc06d1c042753c454b4ece39778798e5c2a.4c732cd9e3bd51c9790128dc15590f2a18e928f4dcbc315c1dffe5231ec45984.lock",
        "280541649472174b9a8bfa31ba0c861e806be14d2f60113b6da0d1fb5ec395bb.c7a1c260ba157336a16a3228f89a319e62669fcbb609e915f81ad0a41cde9a36",
        "231dc7d689812283cb707214f58bffc06d1c042753c454b4ece39778798e5c2a.768ae45466792a0f33057b9bb31f8e8c6cbdbac9d3b2fb504e57ba2ab840a489.lock",
        "eeea462f521dc2d50bc28be24a8993a6f84552c3b0cc16036733b25b00b76eff.b9af6e61147590608619b5508e4a608e12d5907e641fa73ebb9da3ea5f8c1d94",
        "231dc7d689812283cb707214f58bffc06d1c042753c454b4ece39778798e5c2a.4c732cd9e3bd51c9790128dc15590f2a18e928f4dcbc315c1dffe5231ec45984",
        "dbe77a7e08998d5dd16d296d52ac847d948ce8623f9d03521523228adef7738a.f5d5ee4d8c7ca816f3fabd88ce4c54472271b2910a3f09caf4b889aca978f38c.json",
        "fb5a688525d6c40a1f822784bba5c568a6209a7f68bbfd81ad30aee8af9fe757.2bd248ef954b136f33ba3b5f29736fc22fe21299b45a94ae1edd3136a6f1ddb2.lock",
        "fb5a688525d6c40a1f822784bba5c568a6209a7f68bbfd81ad30aee8af9fe757.2bd248ef954b136f33ba3b5f29736fc22fe21299b45a94ae1edd3136a6f1ddb2.json",
        "231dc7d689812283cb707214f58bffc06d1c042753c454b4ece39778798e5c2a.768ae45466792a0f33057b9bb31f8e8c6cbdbac9d3b2fb504e57ba2ab840a489",
        "231dc7d689812283cb707214f58bffc06d1c042753c454b4ece39778798e5c2a.4c732cd9e3bd51c9790128dc15590f2a18e928f4dcbc315c1dffe5231ec45984.json",
        "c82b120b36d8b28738f1a1c0757b7f4872c909ec18453800e48e76412b2a224f.d6d474c4ca928339db0d7a9e8e4663b795225c29b46463593ab08c445ad08fbf.json",
        "231dc7d689812283cb707214f58bffc06d1c042753c454b4ece39778798e5c2a.768ae45466792a0f33057b9bb31f8e8c6cbdbac9d3b2fb504e57ba2ab840a489.json",
        "eeea462f521dc2d50bc28be24a8993a6f84552c3b0cc16036733b25b00b76eff.b9af6e61147590608619b5508e4a608e12d5907e641fa73ebb9da3ea5f8c1d94.json",
    ]

    for f in files:
        if not os.path.exists(os.path.join(root, "{}".format(f))):
            s3.download_file(
                os.environ.get("AiModelBucket"),
                "data_science/ai_model_files/content-moderation-text/version_1/{}".format(
                    f
                ),
                os.path.join(root, "{}".format(f)),
            )
