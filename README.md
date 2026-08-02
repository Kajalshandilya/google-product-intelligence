# Google Product Intelligence — User Adoption & Product Analytics Platform

A Streamlit-based portfolio application for analyzing user adoption, engagement, satisfaction, segmentation, and co-usage patterns across Google products.

## Current dataset

- Rows: 500
- Columns: 10
- Source: Synthetic portfolio data
- File: `google_product_usage_500_synthetic.csv`

## Features

- CSV upload and validation
- Executive analytics dashboard
- Data quality center
- Product adoption analytics
- Product comparison
- User segmentation
- Product co-usage analysis
- Automated data-driven insights
- Rule-based "Ask Your Data" assistant
- Interactive filters

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy for free

1. Create a GitHub repository.
2. Upload:
   - `app.py`
   - `requirements.txt`
   - `google_product_usage_500_synthetic.csv`
3. Open Streamlit Community Cloud.
4. Connect your GitHub account.
5. Select the repository and `app.py`.
6. Deploy.

## Data disclaimer

This application uses synthetic and/or user-provided survey data for portfolio and educational purposes. It is not affiliated with Google and does not use Google's proprietary or internal analytics.

## Suggested next phase

Collect 50–100 genuine survey responses using the same schema, then add:

- Real vs synthetic comparison
- Competitor preference fields
- Product-level non-adoption reasons
- Statistical significance testing
- MySQL/SQL analytical layer
