#!/bin/bash
# Skill Structure Validation Script

echo "🔍 Validating Skill Structure..."
echo ""

STRUCTURE_DIR="/Users/user/Workspace/multi-agent-workflow/shared/skill-structure"
ERRORS=0

# Check core files
echo "📄 Checking core files..."
for file in "STANDARD.md" "CLAUDE.md"; do
    if [ -f "$STRUCTURE_DIR/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check templates
echo ""
echo "📋 Checking templates..."
TEMPLATES=(
    "SKILL.md.template"
    "quickstart.md.template"
    "perspectives.md.template"
    "custom-perspectives.md.template"
    "meta.yaml.template"
    "summary.md.template"
    "phases.yaml.template"
    "quality-gates.yaml.template"
    "README.md"
)

for template in "${TEMPLATES[@]}"; do
    if [ -f "$STRUCTURE_DIR/templates/$template" ]; then
        echo "  ✅ $template"
    else
        echo "  ❌ $template (missing)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All files present and validated!"
    echo ""
    echo "📦 Structure complete:"
    echo "   - 2 core files (STANDARD.md, CLAUDE.md)"
    echo "   - 9 template files"
    echo ""
    echo "🚀 Ready to use!"
else
    echo "❌ Validation failed with $ERRORS error(s)"
    exit 1
fi
