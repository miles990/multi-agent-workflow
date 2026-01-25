#!/usr/bin/env node
/**
 * 模型路由器 - 根據任務複雜度選擇模型
 * 用法: node model-router.js <stage> <perspective>
 */

const fs = require('fs');
const path = require('path');

// 預設路由配置
const DEFAULT_ROUTING = {
  RESEARCH: {
    architecture: 'sonnet',
    cognitive: 'sonnet',
    workflow: 'haiku',
    industry: 'haiku',
    _synthesis: 'sonnet'
  },
  PLAN: {
    architect: 'sonnet',
    'risk-analyst': 'sonnet',
    estimator: 'haiku',
    'ux-advocate': 'haiku',
    _synthesis: 'sonnet'
  },
  TASKS: {
    'dependency-analyst': 'sonnet',
    'task-decomposer': 'haiku',
    'test-planner': 'haiku',
    'risk-preventor': 'haiku',
    _validation: 'sonnet'
  },
  IMPLEMENT: {
    main_agent: 'sonnet',
    'tdd-enforcer': 'haiku',
    'performance-optimizer': 'haiku',
    'security-auditor': 'sonnet',
    maintainer: 'haiku',
    _self_review: 'sonnet'
  },
  REVIEW: {
    'code-quality': 'haiku',
    'test-coverage': 'haiku',
    documentation: 'haiku',
    integration: 'sonnet',
    _synthesis: 'sonnet'
  },
  VERIFY: {
    'functional-tester': 'haiku',
    'edge-case-hunter': 'sonnet',
    'regression-checker': 'haiku',
    'acceptance-validator': 'sonnet',
    _final_report: 'sonnet'
  }
};

// 嘗試載入配置檔案
function loadConfig() {
  const configPaths = [
    path.join(process.cwd(), 'shared/config/model-routing.yaml'),
    path.join(__dirname, '../config/model-routing.yaml')
  ];

  for (const configPath of configPaths) {
    try {
      if (fs.existsSync(configPath)) {
        const yaml = require('js-yaml');
        const content = fs.readFileSync(configPath, 'utf8');
        const config = yaml.load(content);
        return config.routing || DEFAULT_ROUTING;
      }
    } catch (e) {
      // 繼續嘗試下一個路徑
    }
  }

  return DEFAULT_ROUTING;
}

// 獲取路由原因
function getRoutingReason(stage, perspective, model) {
  if (model === 'opus') {
    return '關鍵決策任務，使用最強模型';
  } else if (model === 'sonnet') {
    return '需要深度分析或複雜推理';
  } else if (model === 'haiku') {
    return '較簡單或機械性任務';
  }
  return '預設模型';
}

// 主函數
function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('用法: node model-router.js <stage> <perspective>');
    console.error('範例: node model-router.js RESEARCH architecture');
    process.exit(1);
  }

  const [stage, perspective] = args;
  const routing = loadConfig();

  // 獲取模型
  const stageRouting = routing[stage.toUpperCase()];
  let model = 'sonnet';  // 預設

  if (stageRouting) {
    model = stageRouting[perspective] || stageRouting._default || 'sonnet';
  }

  const result = {
    stage: stage.toUpperCase(),
    perspective,
    model,
    reason: getRoutingReason(stage, perspective, model)
  };

  console.log(JSON.stringify(result, null, 2));
}

main();
