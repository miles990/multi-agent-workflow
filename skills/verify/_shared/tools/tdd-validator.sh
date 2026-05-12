#!/bin/bash
# TDD 驗證器 - 在 IMPLEMENT 階段每個任務前執行
# 用法: ./tdd-validator.sh <TASK_ID> <IMPL_FILE>

set -e

TASK_ID=$1
IMPL_FILE=$2

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 輸出函數
log_error() {
  echo -e "${RED}❌ BLOCKER: $1${NC}"
}

log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

# 檢查參數
if [[ -z "$TASK_ID" || -z "$IMPL_FILE" ]]; then
  echo "用法: $0 <TASK_ID> <IMPL_FILE>"
  echo "範例: $0 T-F-001 src/auth/login.ts"
  exit 1
fi

echo "🔍 TDD 驗證中... 任務: $TASK_ID, 檔案: $IMPL_FILE"

# 1. 判斷測試檔案路徑
# 支援多種命名慣例
determine_test_file() {
  local impl_file=$1
  local test_file=""

  # TypeScript/JavaScript: src/foo.ts -> tests/foo.test.ts
  if [[ "$impl_file" == *.ts ]]; then
    test_file=$(echo "$impl_file" | sed 's/\.ts$/.test.ts/' | sed 's/^src\//tests\//')
    if [[ ! -f "$test_file" ]]; then
      # 嘗試 .spec.ts
      test_file=$(echo "$impl_file" | sed 's/\.ts$/.spec.ts/')
    fi
  elif [[ "$impl_file" == *.js ]]; then
    test_file=$(echo "$impl_file" | sed 's/\.js$/.test.js/' | sed 's/^src\//tests\//')
  elif [[ "$impl_file" == *.py ]]; then
    # Python: foo.py -> test_foo.py
    local dir=$(dirname "$impl_file")
    local base=$(basename "$impl_file" .py)
    test_file="$dir/test_$base.py"
    if [[ ! -f "$test_file" ]]; then
      test_file="${dir}/${base}_test.py"
    fi
  fi

  echo "$test_file"
}

TEST_FILE=$(determine_test_file "$IMPL_FILE")

# 2. 檢查測試檔案是否存在
if [[ -z "$TEST_FILE" ]]; then
  log_error "無法判斷測試檔案路徑"
  exit 1
fi

if [[ ! -f "$TEST_FILE" ]]; then
  log_error "測試檔案不存在: $TEST_FILE"
  echo ""
  echo "TDD 要求先建立測試，再進行實作。"
  echo "請建立測試檔案: $TEST_FILE"
  exit 1
fi

log_success "測試檔案存在: $TEST_FILE"

# 3. 檢查測試是否可執行
echo ""
echo "🧪 檢查測試是否可執行..."

run_test() {
  local test_file=$1

  if [[ "$test_file" == *.ts ]] || [[ "$test_file" == *.js ]]; then
    # Node.js 測試
    if [[ -f "package.json" ]]; then
      if grep -q "vitest" package.json 2>/dev/null; then
        npx vitest run "$test_file" --passWithNoTests 2>/dev/null
      elif grep -q "jest" package.json 2>/dev/null; then
        npx jest "$test_file" --passWithNoTests 2>/dev/null
      else
        log_warning "未偵測到測試框架，跳過執行檢查"
        return 0
      fi
    fi
  elif [[ "$test_file" == *.py ]]; then
    # Python 測試
    python -m pytest "$test_file" --collect-only 2>/dev/null
  fi
}

if run_test "$TEST_FILE"; then
  log_success "測試可執行"
else
  log_error "測試無法執行，請確認測試語法正確"
  exit 1
fi

# 4. 檢查測試是否定義了預期行為
echo ""
echo "📋 檢查測試內容..."

check_test_content() {
  local test_file=$1
  local has_test=false

  # 檢查是否有測試定義
  if grep -qE "(describe|it|test|def test_)" "$test_file" 2>/dev/null; then
    has_test=true
  fi

  if [[ "$has_test" == true ]]; then
    log_success "測試定義了預期行為"
    return 0
  else
    log_warning "測試檔案可能缺少測試定義"
    return 0  # 警告但不阻擋
  fi
}

check_test_content "$TEST_FILE"

# 5. 總結
echo ""
echo "═══════════════════════════════════════════"
log_success "TDD 驗證通過，可以開始實作"
echo "任務: $TASK_ID"
echo "實作檔案: $IMPL_FILE"
echo "測試檔案: $TEST_FILE"
echo "═══════════════════════════════════════════"

exit 0
