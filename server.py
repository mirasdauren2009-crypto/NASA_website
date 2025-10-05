from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from io import BytesIO
from astropy.io import fits
from tsfresh import extract_features
from tsfresh.feature_extraction import MinimalFCParameters
import xgboost as xgb
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# --- Load the trained XGBoost model ---
model = xgb.XGBClassifier()
model.load_model("public/xgb_model9221.json")  # replace with your model filename


@app.route("/predict", methods=["POST"])
def predict():
    try:
        # --- 1️⃣ Parse numeric fields from form ---
        form = request.form
        features = {key: float(form.get(key, 0) or 0) for key in [
            "koi_time0bk", "koi_period", "koi_duration", "koi_srad", "koi_prad",
            "koi_teq", "koi_depth", "koi_time0bk_err1", "koi_time0bk_err2",
            "koi_period_err1", "koi_period_err2", "koi_duration_err1",
            "koi_duration_err2", "koi_srad_err1", "koi_srad_err2",
            "koi_prad_err1", "koi_prad_err2", "koi_teq_err1", "koi_teq_err2",
            "koi_depth_err1", "koi_depth_err2"
        ]}

        koi_time0bk = features["koi_time0bk"]
        koi_period = features["koi_period"]
        koi_duration = features["koi_duration"]

        # --- 2️⃣ Load and process uploaded FITS file ---
        fits_file = request.files.get("fits_file")
        if fits_file is None:
            return jsonify({"error": "No FITS file uploaded"}), 400

        with fits.open(BytesIO(fits_file.read()), mode="readonly") as hdul:
            data = hdul[1].data

            # Safe dtype conversion for NumPy 2.0+
            def to_native(x):
                if x.dtype.byteorder == ">":
                    return x.byteswap().view(x.dtype.newbyteorder("="))
                return x

            time = np.array(to_native(data["TIME"]))
            flux = np.array(to_native(data["PDCSAP_FLUX"]))

        mask = ~np.isnan(time) & ~np.isnan(flux)
        if not np.any(mask):
            return jsonify({"error": "No valid time/flux data in FITS"}), 400

        time = time[mask]
        flux = flux[mask]

        # --- 3️⃣ Slice time-series around expected transit ---
        duration_days = koi_duration / 24
        window_factor = 1.5
        num_transits = int((time[-1] - koi_time0bk) / koi_period) + 1
        transit_centers = koi_time0bk + np.arange(num_transits) * koi_period

        transit_mask = np.zeros_like(time, dtype=bool)
        for t0 in transit_centers:
            transit_mask |= (time >= t0 - window_factor * duration_days / 2) & \
                            (time <= t0 + window_factor * duration_days / 2)

        if not np.any(transit_mask):
            return jsonify({"error": "No transit window found in FITS data"}), 400

        df = pd.DataFrame({
            "id": [0] * np.sum(transit_mask),
            "time": time[transit_mask],
            "flux": flux[transit_mask]
        })

        # --- 4️⃣ Extract features using tsfresh ---
        tsfresh_feats = extract_features(
            df,
            column_id="id",
            column_sort="time",
            default_fc_parameters=MinimalFCParameters(),
            disable_progressbar=True
        )
        tsfresh_feats.reset_index(drop=True, inplace=True)

        # --- 5️⃣ Combine numeric + tsfresh features ---
        full_features = pd.concat(
            [pd.DataFrame([features]), tsfresh_feats], axis=1
        ).fillna(0)

        # --- 6️⃣ Predict with model ---
        proba = float(model.predict_proba(full_features)[0][1]) * 100

        return jsonify({"classification": proba})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Flask server running at http://127.0.0.1:5000")
    app.run(debug=True)
