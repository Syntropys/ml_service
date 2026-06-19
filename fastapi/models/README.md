# Model Files

This directory contains the ML model files used by the Agrolytics ML Bridge API.

## Disease Detection (`disease/`)

TFLite models for the Soft Voting Ensemble (DenseNet121 + MobileNetV2).

### Required Files
| File | Size | Source |
|------|------|--------|
| `mobilenet_v1.tflite` | ~9.7 MB | [Google Drive](https://drive.google.com/drive/folders/16dD8uWfEgzGmnSivoeHQ5gGtINxSsL_T?usp=drive_link) |
| `densenet.tflite` | ~27.6 MB | [Google Drive](https://drive.google.com/drive/folders/16dD8uWfEgzGmnSivoeHQ5gGtINxSsL_T?usp=drive_link) |
| `class_mapping.json` | <1 KB | ✅ Included |
| `ensemble_config.json` | <1 KB | ✅ Included |

### Download Instructions
1. Open the Google Drive link above
2. Download `mobilenet_v1.tflite` and `densenet.tflite`
3. Place them in `fastapi/models/disease/`

## Predictive Analytics (`predictive/`)

XGBoost model for yield prediction.

### Required Files
| File | Size | Status |
|------|------|--------|
| `xgboost.joblib` | 0.47 MB | ✅ Included |

## Architecture
```
models/
├── disease/
│   ├── mobilenet_v1.tflite      ← Download from Google Drive
│   ├── densenet.tflite          ← Download from Google Drive
│   ├── class_mapping.json       ✅ Included
│   └── ensemble_config.json     ✅ Included
└── predictive/
    └── xgboost.joblib           ✅ Included
```

> **Note**: TFLite files are not committed to git due to size. The API
> will start without them but disease detection will return an error.
> Predictive analytics will work immediately.
