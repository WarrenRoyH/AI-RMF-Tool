#!/bin/sh

# AI-RMF Lifecycle Tools: Bootstrap Script
# Goal: Setup uv, Python, System Dependencies, and the AI-RMF Workspace.

set -e

# --- 0. Set Defaults ---
FLAVOR=${FLAVOR:-"full"}
SANDBOX=${SANDBOX:-"none"}
RUN_TESTS=false

# --- Parse Arguments ---
for i in "$@"; do
  case $i in
    --test)
      RUN_TESTS=true
      shift
      ;;
  esac
done

# --- Colors for Output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "${BLUE}==> Initializing AI-RMF Lifecycle Workspace...${NC}"

# --- 0. System Dependencies ---
# (Removed apt-get/brew dependencies to rely on pure Python alternatives via uv)

# --- 1. Check for uv ---
if ! command -v uv >/dev/null 2>&1; then
  echo "--> ${BLUE}uv not found. Installing uv locally...${NC}"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Add to path for this session
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "--> ${GREEN}uv is already installed.${NC}"
fi

# --- 2. Create Workspace Structure ---
echo "--> ${BLUE}Creating project structure...${NC}"
mkdir -p workspace/logs workspace/reports config core librarian scripts sentry
touch workspace/project-manifest.json

# --- 3. Initialize Python Environment ---
echo "--> ${BLUE}Setting up isolated Python environment (Python 3.11)...${NC}"
uv venv --python 3.11 .venv --clear
. .venv/bin/activate

# --- 4. Install Dependencies (Modular Tiers) ---
echo "--> ${BLUE}Installing AI-RMF dependencies (Tier: $FLAVOR)...${NC}"
uv pip install pip python-dotenv questionary litellm pydantic psutil numpy==2.2.3

if [ "$FLAVOR" = "minimal" ]; then
  echo "--> ${GREEN}Minimal Tier: Governance & Core LLM connectivity only.${NC}"
fi

if [ "$FLAVOR" = "standard" ] || [ "$FLAVOR" = "full" ]; then
  echo "--> ${BLUE}Standard Tier: Adding Security Scanning & Guardrails...${NC}"
  # Use transformers 4.57.6 to fix CVEs while maintaining compatibility
  # with llm-guard which requires the 4.x TFPreTrainedModel.
  uv pip install garak llm-guard transformers==4.57.6 tf-keras pip-audit spacy
fi

if [ "$FLAVOR" = "full" ]; then
  echo "--> ${BLUE}Full Tier: Adding Observatory (Arize-Phoenix) & Export Tools...${NC}"
  # xhtml2pdf is a pure Python replacement for wkhtmltopdf/pdfkit
  # Note: xhtml2pdf -> svglib -> pycairo requires system cairo headers.
  # We try to install it but continue if it fails.
  uv pip install arize-phoenix markdown || true
  uv pip install xhtml2pdf || echo "${RED}[Warning] xhtml2pdf failed to install (requires system cairo). PDF export will be unavailable.${NC}"
fi

# Install promptfoo via npm if available
if command -v npm >/dev/null 2>&1; then
  echo "--> ${BLUE}Installing promptfoo globally...${NC}"
  npm install -g promptfoo --quiet
else
  echo "--> ${RED}[Warning] npm not found. Promptfoo benchmarking will require manual installation.${NC}"
fi

# Pre-download NLP models to prevent runtime 'No module named pip' errors
echo "--> ${BLUE}Pre-loading NLP models for Sentry...${NC}"
. .venv/bin/activate
# Force numpy 2.2.3 again as it may have been downgraded by garak/llm-guard
uv pip install numpy==2.2.3 --quiet
python3 -m spacy download en_core_web_lg --quiet

# --- 5. Configure Sandbox (Context Only for now) ---
if [ "$SANDBOX" = "strict" ]; then
  echo "--> ${GREEN}Strict Sandbox requested.${NC}"
  if command -v bwrap >/dev/null 2>&1; then
    echo "    [Verified] Bubblewrap is available for Linux isolation."
  elif [ "$(uname)" = "Darwin" ]; then
    echo "    [Verified] macOS sandbox-exec is available."
  else
    echo "    ${RED}[Warning] No native sandbox tool found. Falling back to unprivileged user mode.${NC}"
  fi
fi

# --- 6. Interactive API Setup ---
echo ""
if [ ! -f .env ]; then
  echo "--> ${BLUE}Step 0.5: LLM Configuration${NC}"
  echo "Select your preferred LLM provider:"
  echo "  1) OpenAI (GPT-5.4 Pro, GPT-5 Nano)"
  echo "  2) Anthropic (Claude 4.6 Sonnet, Haiku)"
  echo "  3) Google (Gemini 3.1 Flash-Lite, 3.1 Pro)"
  echo "  4) Local (Ollama / vLLM)"
  echo "  5) Custom / Other"

  read -p "Choice [1-5]: " CHOICE

  case $CHOICE in
    1)
      MODEL="gpt-5.4-pro"
      KEY_NAME="OPENAI_API_KEY"
      ;;
    2)
      MODEL="claude-4-sonnet-20260217"
      KEY_NAME="ANTHROPIC_API_KEY"
      ;;
    3)
      MODEL="gemini/gemini-3.1-flash-lite-preview"
      KEY_NAME="GOOGLE_API_KEY"
      ;;

    4)
      MODEL="ollama/llama3"
      KEY_NAME="NONE"
      echo "Note: Ensure Ollama is running at http://localhost:11434"
      ;;
    5)
      read -p "Enter model ID (e.g. gpt-4): " MODEL
      read -p "Enter API key variable name (e.g. OPENAI_API_KEY): " KEY_NAME
      ;;
    *)
      echo "${RED}Invalid choice. Defaulting to OpenAI.${NC}"
      MODEL="gpt-4o"
      KEY_NAME="OPENAI_API_KEY"
      ;;
  esac

  echo "AI_RMF_MODEL=$MODEL" > .env
  
  if [ "$KEY_NAME" != "NONE" ]; then
    read -p "Enter your $KEY_NAME: " API_KEY
    echo "$KEY_NAME=$API_KEY" >> .env
  fi

  echo "${GREEN}--> .env file created successfully.${NC}"
else
  echo "--> ${GREEN}.env file already exists.${NC}"
fi

# --- 7. Final Hand-off ---
if [ "$RUN_TESTS" = true ]; then
  echo ""
  echo "${BLUE}==> [REGRESSION]: Running automated test suite...${NC}"
  . .venv/bin/activate
  python3 -m pytest tests/
  echo "${GREEN}==> All tests passed successfully.${NC}"
  exit 0
fi

echo ""
echo "${GREEN}==============================================${NC}"
echo "${GREEN}   AI-RMF WORKSPACE INITIALIZATION COMPLETE   ${NC}"
echo "${GREEN}==============================================${NC}"
echo ""
echo "How would you like to proceed?"
echo "  1) Start Phase 1: GOVERN (Configure your project policies)"
echo "  2) Run AUTOPILOT (Full end-to-end security pipeline)"
echo "  3) Exit and run manually later"

read -p "Choice [1-3]: " FINAL_CHOICE

case $FINAL_CHOICE in
  1)
    ./ai-rmf govern
    ;;
  2)
    ./ai-rmf autopilot
    ;;
  *)
    echo "Setup complete. You can run the tool anytime using './ai-rmf'."
    ;;
esac
