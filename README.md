# Speech to Insight

This project is a basic Flask application that uses MongoDB to store summaries. It provides API endpoints to create, retrieve, and delete summaries.

## Prerequisites

- Python 3.6+
- MongoDB

## Setup

1. **Clone the repository**:

   ```sh
   git clone https://github.com/yourusername/speech-to-insight.git
   cd speech-to-insight
   ```

2. **Install the required packages**:

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the Flask application**:
   ```sh
   python app.py
   ```

## Testing

You can use Postman to test the API endpoints.

## Pages

### Add Recordings

### Check AI Summary

### Tools

1. Create summary (/api/summaries)

2. Get all summaries (/api/summaries)

3. Delete summary by ID (/api/summaries)

4. Search summaries by date (/api/summaries/date_filter)
   ?date=YYYY-MM-DD (summaries equaling the date)
   ?date=YYYY-MM-DD&type=before (summaries before date)
   ?date=YYYY-MM-DD&type=after (summaries after date)

5. Serach summaries by key terms (case-insensitive) (api/summaries/key_term_search)
   ?key_terms=...&key_terms=...

### Worktable

## License

This project is licensed under the MIT License.
