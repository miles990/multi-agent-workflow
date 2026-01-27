# 認知研究員 報告

## 核心發現

1. **分層觸發架構**：系統採用三層觸發決策模型（Command → Mention → Activation），每層有獨立的認知決策點，形成漸進式注意力機制（Progressive Attention Model）。

2. **上下文新鮮度管理**：透過 Session 系統實現記憶持久化與過期策略，使用 LRU + 時間戳雙重機制維護對話歷史，減少用戶重新建立上下文的認知負擔。

3. **自適應回應反饋**：Typing indicator + Heartbeat 機制提供持續的系統狀態反饋，減少「黑盒焦慮」（Black Box Anxiety），增強用戶對 AI 行為的可預測性。

4. **認知負荷最小化設計**：命令系統採用多層級別名（text alias + native command + 簡寫）降低記憶負擔，支援不完美輸入（大小寫不敏感、前後綴容錯）。

5. **群組互動心智模型**：Always-on 模式與 Mention-only 模式對應不同的社交期望（主動參與者 vs. 被動助手），系統透過 Group Intro Prompt 明確告知 AI 當前角色定位。

## 詳細分析

### 觸發機制分析：三層決策模型

系統的觸發機制並非單一開關，而是一個**分層的認知決策系統**：

#### 第一層：Command Detection（命令檢測）
```typescript
// commands-registry.ts
export function maybeResolveTextAlias(raw: string, cfg?: ClawdbotConfig)
export function resolveTextCommand(raw: string, cfg?: ClawdbotConfig)
```

**認知設計原理**：
- 斜線命令（`/reset`, `/status`, `/model`）作為**明確意圖信號**（Explicit Intent Signal）
- 支援別名系統減少記憶負擔：`/thinking` = `/think` = `/t`
- 大小寫不敏感 + 前後空白容錯，降低輸入精確度要求
- 冒號語法兼容性（`/command: args` → `/command args`）適應不同用戶習慣

**心智模型**：用戶將命令視為「與系統對話」而非「與 AI 對話」，這是元層級的控制介面。

#### 第二層：Mention Detection（提及檢測）
```typescript
// mentions.ts
export function matchesMentionWithExplicit(params: {
  text: string;
  mentionRegexes: RegExp[];
  explicit?: ExplicitMentionSignal;
}): boolean
```

**認知設計原理**：
- 支援多種 Mention 模式：`@name`、emoji、自定義 regex pattern
- 顯式與隱式 mention 分離：平台原生 mention（explicit）優先，文字模式（regex）補充
- Unicode 正規化處理（移除零寬字元），防止視覺欺騙攻擊

**社交認知**：在群組場景中，mention 是「注意力分配」的社交信號，對應人類群聊中的「點名」行為。

#### 第三層：Activation Mode（激活模式）
```typescript
// group-activation.ts
export type GroupActivationMode = "mention" | "always";

// groups.ts
export function buildGroupIntro(params): string {
  const activationLine =
    activation === "always"
      ? "Activation: always-on (you receive every group message)."
      : "Activation: trigger-only (you are invoked only when explicitly mentioned; recent context may be included).";
}
```

**認知設計原理**：
- `mention` 模式：AI 作為「被動助手」，僅在被召喚時出現
- `always` 模式：AI 作為「主動參與者」，持續關注對話流
- 模式轉換透過 `/activation` 命令，用戶可動態調整 AI 的「在場感」（Presence）

**社交心理學映射**：
- `mention` = 「專家顧問」角色：需要時才提供意見
- `always` = 「團隊成員」角色：持續參與討論，但需要學會何時保持沉默

### 命令系統設計：降低認知負荷

#### 多層級別名系統
```typescript
// commands-registry.data.ts
defineChatCommand({
  key: "think",
  nativeName: "think",
  textAlias: "/think",
})
registerAlias(commands, "think", "/thinking", "/t");
```

**認知原理**：Miller's Law（人類短期記憶容量 7±2 項）
- 提供多個入口點降低記憶門檻
- 簡寫形式（`/t`）降低高頻操作的摩擦力
- 完整形式（`/thinking`）提供語義明確性

#### 參數解析寬容性
```typescript
// commands-registry.ts
export function normalizeCommandBody(raw: string, options?: CommandNormalizeOptions): string {
  // 支援冒號語法：/command: args → /command args
  const colonMatch = singleLine.match(/^\/([^\s:]+)\s*:(.*)$/);

  // 支援 @botname 提及：/command@botname → /command
  const mentionMatch = normalizedBotUsername
    ? normalized.match(/^\/([^\s@]+)@([^\s]+)(.*)$/)
    : null;
}
```

**用戶體驗哲學**：系統應該理解用戶意圖，而非要求用戶精確匹配語法。

#### 命令發現性（Discoverability）
```typescript
defineChatCommand({
  key: "tts",
  argsMenu: {
    arg: "action",
    title:
      "TTS Actions:\n" +
      "• On – Enable TTS for responses\n" +
      "• Off – Disable TTS\n" +
      // ... 提供內嵌式說明文件
  },
})
```

**認知設計**：減少「查文件」的外部認知負荷，將說明內嵌於互動流程中。

### 上下文管理：記憶持久化與新鮮度

#### Session 狀態管理
```typescript
// session.ts
export async function initSessionState(params): Promise<SessionInitResult> {
  const freshEntry = entry
    ? evaluateSessionFreshness({ updatedAt: entry.updatedAt, now, policy: resetPolicy }).fresh
    : false;

  if (!isNewSession && freshEntry) {
    sessionId = entry.sessionId;
    systemSent = entry.systemSent ?? false;
    abortedLastRun = entry.abortedLastRun ?? false;
    persistedThinking = entry.thinkingLevel;
    // ... 恢復先前的 session 狀態
  } else {
    sessionId = crypto.randomUUID();
    isNewSession = true;
    // ... 建立新 session
  }
}
```

**認知原理**：
- **Session 新鮮度評估**：時間戳 + 策略判斷，自動決定是恢復舊對話還是開啟新對話
- **狀態持久化**：thinking level、verbose mode、model override 等偏好設定跨對話保留
- **Reset Triggers**：`/new`、`/reset` 提供明確的「記憶重置」信號

**心智模型映射**：
- 新對話 = 「從頭開始解釋」
- 舊對話恢復 = 「接續上次討論」
- 用戶不需要明確告知「你還記得我們上次談的內容嗎？」

#### 群組歷史管理
```typescript
// history.ts
export const MAX_HISTORY_KEYS = 1000;

export function evictOldHistoryKeys<T>(
  historyMap: Map<string, T[]>,
  maxKeys: number = MAX_HISTORY_KEYS,
): void {
  if (historyMap.size <= maxKeys) return;
  const keysToDelete = historyMap.size - maxKeys;
  const iterator = historyMap.keys();
  for (let i = 0; i < keysToDelete; i++) {
    const key = iterator.next().value;
    if (key !== undefined) historyMap.delete(key);
  }
}
```

**認知設計**：
- LRU eviction：優先保留最近活躍的對話上下文
- 硬性上限（1000 keys）防止無限增長
- 歷史上下文標記：`[Chat messages since your last reply - for context]` 明確告知 AI 哪些是背景、哪些是當前訊息

**降低認知負荷**：
- 用戶不需要手動「清理歷史」
- 系統自動維護合理的記憶窗口
- 在群組場景中，AI 能看到「對話流」而非孤立訊息

### 用戶體驗考量：降低認知負荷與提升可預測性

#### Typing Indicator：持續反饋機制
```typescript
// typing.ts
export function createTypingController(params: {
  typingIntervalSeconds?: number;  // 預設 6 秒
  typingTtlMs?: number;             // 預設 2 分鐘
}): TypingController {
  const startTypingLoop = async () => {
    refreshTypingTtl();
    if (typingTimer) return;
    await ensureStart();
    typingTimer = setInterval(() => {
      void triggerTyping();
    }, typingIntervalMs);
  };
}
```

**認知心理學原理**：
- **可見性反饋**（Visibility of System Status）：用戶能看到「系統正在思考」
- **減少焦慮**：長時間靜默會產生「是不是壞掉了？」的不確定感
- **時間感知扭曲**：有反饋的等待比無反饋的等待感覺更短
- **TTL 機制**：防止「永久 typing」的異常狀態，2 分鐘後自動停止

#### Heartbeat：主動維護機制
```typescript
// heartbeat.ts
export const HEARTBEAT_PROMPT =
  "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.";

export function stripHeartbeatToken(raw?: string, opts): { shouldSkip: boolean; text: string; didStrip: boolean } {
  // 識別 HEARTBEAT_OK token，判斷是否應該跳過回覆
}
```

**設計理念**：
- **主動維護**：AI 定期檢查是否有待辦任務（類似 cron job）
- **沉默協議**：`HEARTBEAT_OK` token 表示「無事可報」，系統不會產生空洞的回應
- **防止幻覺**：明確指示「不要從舊對話中推測任務」，避免 AI 自行發明工作

**用戶心智模型**：AI 不是「被動工具」而是「主動助手」，會在背景檢查是否有事情需要處理。

#### 群組互動的社交認知
```typescript
// groups.ts
export function buildGroupIntro(params): string {
  const silenceLine =
    activation === "always"
      ? `If no response is needed, reply with exactly "${params.silentToken}" (and nothing else) so Clawdbot stays silent.`
      : undefined;

  const lurkLine =
    "Be a good group participant: mostly lurk and follow the conversation; reply only when directly addressed or you can add clear value.";
}
```

**社交心理學設計**：
- **群組禮儀教學**：明確告訴 AI「不要過度活躍」
- **沉默 Token**：提供一個「我看到了但不需要回應」的機制
- **價值過濾**：鼓勵 AI 評估「我的回應是否真的有用？」

**降低社交摩擦**：
- 防止 AI 成為「話癆」（spam）
- 模擬人類群組互動的「觀察→判斷→發言」流程
- 提供 emoji reaction 作為低成本的參與方式

### 錯誤處理與降級策略

#### 快速中止機制
```typescript
// abort.ts
const ABORT_TRIGGERS = new Set(["stop", "esc", "abort", "wait", "exit", "interrupt"]);

export async function tryFastAbortFromMessage(params): Promise<{ handled: boolean; aborted: boolean; stoppedSubagents?: number }> {
  const abortRequested = normalized === "/stop" || isAbortTrigger(stripped);
  if (!abortRequested) return { handled: false, aborted: false };

  // 中止主 session
  const aborted = sessionId ? abortEmbeddedPiRun(sessionId) : false;

  // 中止所有 subagents
  const { stopped } = stopSubagentsForRequester({ cfg, requesterSessionKey });
}
```

**認知設計**：
- **多種停止指令**：`stop`、`esc`、`abort`、`wait`、`exit`、`interrupt` 覆蓋不同用戶習慣
- **即時回應**：不需要等待 AI 完成，立即中止
- **連鎖停止**：自動停止所有關聯的 subagent 執行

**心理安全感**：
- 用戶感到「我隨時可以停止失控的 AI」
- 降低「AI 自主執行」的焦慮感

#### Session 記憶與恢復
```typescript
// session.ts
sessionEntry = {
  sessionId,
  updatedAt: Date.now(),
  systemSent,
  abortedLastRun,  // 記錄上次是否被中止
  thinkingLevel: persistedThinking ?? baseEntry?.thinkingLevel,
  verboseLevel: persistedVerbose ?? baseEntry?.verboseLevel,
  // ... 其他持久化狀態
}
```

**錯誤恢復設計**：
- `abortedLastRun` flag：告知系統「上次執行被中止」
- 狀態持久化：即使中止，用戶偏好設定不會丟失
- Session 分支（fork）：對話可以從特定時間點分支

**認知友善性**：
- 錯誤不會導致「從頭開始」
- 用戶可以「修正後重試」而非「放棄」

## 建議與洞察

### 1. 認知負荷階梯設計（Cognitive Load Ladder）

**當前設計的亮點**：
- **新手友善**：命令有完整名稱（`/thinking`）、簡寫（`/t`）、native command 三種形式
- **容錯性高**：大小寫不敏感、前後空白自動處理、冒號語法兼容

**建議**：
- 考慮加入 **命令建議系統**（Command Suggestion）：當用戶輸入 `/thi`，系統提示 `Did you mean /think or /thinking?`
- **使用頻率學習**：追蹤用戶最常用的命令，動態調整建議順序

### 2. 群組互動的社交認知模型

**當前設計的亮點**：
- `always` vs. `mention` 模式對應不同的社交期望
- 明確的「沉默協議」（SILENT_REPLY_TOKEN）
- 群組禮儀指南（"mostly lurk", "add clear value"）

**建議**：
- **自適應激活模式**：在 `always` 模式下，若 AI 連續 N 次使用 SILENT_TOKEN，系統可建議切換到 `mention` 模式（「看起來你不需要我持續關注，要改成僅在提及時回應嗎？」）
- **對話流感知**：當群組正在進行快速多人對話時，自動提高 AI 的「沉默閾值」，避免打斷流暢的人際互動

### 3. 上下文新鮮度與記憶管理

**當前設計的亮點**：
- Session freshness evaluation 自動判斷是否恢復舊對話
- LRU eviction 防止無限增長
- 歷史上下文標記明確區分背景與當前訊息

**建議**：
- **記憶摘要機制**：對於長期 session，定期生成「對話摘要」取代完整歷史，減少 token 消耗
- **話題轉換檢測**：當檢測到話題變化（如從「討論程式碼」轉到「閒聊」），自動標記 session 分段
- **主動記憶提示**：當 session 恢復時，AI 主動總結「我們上次談到...」，減少用戶重新建立上下文的負擔

### 4. 錯誤處理與系統透明度

**當前設計的亮點**：
- 多種 abort trigger 覆蓋不同用戶習慣
- Typing indicator 提供持續反饋
- `abortedLastRun` flag 記錄錯誤狀態

**建議**：
- **錯誤分類回報**：當 abort 發生時，簡要說明原因（「因長時間無回應被中止」vs.「因用戶命令被中止」）
- **自動重試建議**：若檢測到非用戶意圖的錯誤（如網路問題），提供「要重試嗎？」的快速按鈕
- **狀態可視化**：在 `/status` 命令中顯示「當前 session 健康度」（token 使用量、上次更新時間、是否有未完成的工作）

### 5. 認知負荷的動態調整

**洞察**：不同用戶、不同場景對「系統反饋」的需求不同
- 新手需要更多指引和反饋
- 專家希望減少干擾，快速執行

**建議**：
- **學習模式（Learning Mode）**：啟用時，系統會主動解釋「我為什麼這樣做」（類似 verbose mode 但更聚焦於決策原因）
- **專家模式（Expert Mode）**：減少確認提示、提供批次操作、支援命令管線
- **自動模式判斷**：追蹤用戶熟練度（命令使用頻率、錯誤率），動態調整提示詳細度

## 風險/注意事項

### 1. 群組場景的過度活躍風險

**風險描述**：
- 在 `always` 模式下，AI 可能過度參與，成為「話癆」
- 即使有 SILENT_TOKEN，AI 可能誤判「何時該沉默」

**緩解措施**：
- 強化 Group Intro 的「沉默指引」
- 追蹤 SILENT_TOKEN 使用率，若過低（< 30%）發出警告
- 提供「群組反饋機制」：其他成員可以 `/feedback too_active` 告知 AI 過度活躍

### 2. Session 狀態持久化的隱私風險

**風險描述**：
- Session store 儲存大量對話歷史與用戶偏好
- 若存取控制不當，可能洩露敏感資訊

**緩解措施**：
- Session store 應加密儲存
- 定期清理過期 session（實施 TTL 策略）
- 提供 `/privacy clear` 命令，用戶可主動清除歷史

### 3. 命令別名系統的可發現性問題

**風險描述**：
- 多層級別名雖降低記憶負荷，但也可能造成混亂
- 用戶可能不知道 `/t` = `/think` = `/thinking`

**緩解措施**：
- `/help` 命令應同時顯示所有別名
- 在回應中使用「標準形式」（如回應 `/t` 時顯示「Thinking level changed（/think）」）
- 提供 `/commands --aliases` 列出所有別名對應

### 4. Typing Indicator 的異常狀態

**風險描述**：
- 若 AI 執行失敗但未正確清理，typing indicator 可能永久顯示
- 造成「系統卡住」的錯誤印象

**緩解措施**：
- TTL 機制（當前已實作：2 分鐘自動停止）
- 提供 `/status` 命令檢查 typing 狀態
- 實施 watchdog timer，定期檢查是否有「殭屍 typing」

### 5. 上下文視窗的邊界處理

**風險描述**：
- 當歷史上下文過長，可能超出 AI 的 context window
- 突然截斷歷史可能導致 AI 失去關鍵資訊

**緩解措施**：
- 實施「智慧截斷」：保留最近的 N 條訊息 + 話題摘要
- 當接近 context limit 時，主動提示用戶「對話過長，建議開啟新 session」
- 支援「分段回顧」：`/review history` 生成先前對話的摘要

### 6. 多模態互動的認知一致性

**風險描述**：
- Native command（Telegram/Discord/Slack 的原生斜線命令）與 text command（文字輸入的斜線命令）行為不一致
- 用戶在不同平台切換時可能困惑

**緩解措施**：
- 確保兩種模式的命令行為完全一致（當前 `shouldHandleTextCommands` 已處理）
- 在平台不支援 native command 時，自動 fallback 到 text command
- 提供 `/platform` 命令顯示當前平台的特殊行為

---

## 總結

clawdbot 的主動回報系統展現了**以人為中心的 AI 互動設計**（Human-Centered AI Interaction Design）的多個核心原則：

1. **漸進式複雜度**：從簡單的命令到複雜的 session 管理，系統提供多層級的互動介面
2. **認知負荷最小化**：命令別名、容錯解析、上下文持久化都減少用戶的記憶與操作負擔
3. **可見性與反饋**：Typing indicator、heartbeat、abort 機制提供持續的系統狀態可見性
4. **社交認知映射**：群組互動模式對應真實的社交期望，AI 學會「何時該說話、何時該沉默」
5. **錯誤恢復友善**：即使出錯，用戶也不會「失去一切」，session 狀態持久化保障連續性

這個系統的設計哲學是：**AI 不應該是一個需要精確指令的機器，而是一個能理解模糊意圖、提供持續反饋、適應不同社交場景的智能助手**。

從認知科學角度看，這是一個**降低用戶認知負荷、提升系統可預測性、增強心理安全感**的典範設計。
