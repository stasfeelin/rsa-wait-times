# RSA Driving Test Wait Times

A simple dashboard showing estimated waiting times for all RSA driving test centres in Ireland.

🔗 **Live site:** [https://stas.github.io/rsa-wait-times](https://stas.github.io/rsa-wait-times)

## How it works

- A Python scraper (`scraper.py`) fetches data from the [RSA estimator portal](https://rsa.powerappsportals.com/drivertest-estimation-personal/#test-centres)
- A GitHub Actions workflow runs weekly (every Monday) and commits updated data
- A static HTML page (hosted on GitHub Pages) renders the data as a bar chart

## Data source

The RSA provides a public "test centre waiting times" tool that estimates how long you'd wait if you joined the queue today. This scraper calls the same APIs that tool uses — no personal data or login required.

## Running locally

```bash
python3 scraper.py
# Then open index.html in a browser
```

## License

MIT
