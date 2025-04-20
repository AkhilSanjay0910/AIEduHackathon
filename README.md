# streamlit-AI-planner
### 1. Create an API Key

If you don’t already have the necessary API key, follow these steps to get it from the respective API provider:
- Go to https://platform.openai.com/api-keys
- Sign up or log in to your account
- Navigate to the API section and create a new API key
- Copy the API key (you'll need it in the next step)
- Since Canvas access token is only accessible to a student with canvas account, providing the API access token here. Exercise caution while using it!

### 2. Add the API Key to Your Environment

#### Option A: Using `.env` File (Recommended)

1. **Create a `.env` file** in the root directory of your cloned project.

   ```plaintext
   # .env file (do not push to GitHub!)
  OPENAI_API_KEY=your-api-key-here
  CANVAS_TOKEN="9195~XmMAC7URnxn9t9R6MCnkGYvGcM78mwxcUyDXW9mMRQACfx7XGfMrPL9BA7QaNL3r"

  ### 3. Run the application: streamlit run planner_form_1.py