# EXPERIMENTS

## 1) 创建实验
1. 准备 params JSON（可只覆盖需要调的字段）。
2. 调用 `POST /admin/experiments`：
```json
{
  "name": "gsti_v1_calib_k8_x0_0.5",
  "description": "baseline calibration",
  "model_version": "v1",
  "params": {
    "v1": {
      "calibration": {"k": 8, "x0": 0.5}
    }
  },
  "is_active": true
}
```
3. 所有 `/admin/*` 需要 `X-Admin-Key`。

## 2) 分流
- 调用 `POST /experiments/assign`，传 `{user_key, experiment_name}`。
- 已分配用户返回同一 variant（sticky）；新用户按 50/50 分流。

## 3) 评估与 run 记录
- `POST /risk/evaluate` 可传 `experiment_id/variant/user_key`。
- 传入 experiment 后会：
  - 用 `experiments.params` 覆盖默认 GSTI 配置；
  - 写入 `experiment_runs`；
  - 返回 `experiment` 元信息。

## 4) 标注
- `POST /admin/labels` 保存人工 `risk_score_label`、`confidence_label`、`notes`、`factor_overrides`。
- `GET /admin/labels?assessment_id=...` 查看单条评估相关标注。
- `GET /admin/labels/recent?limit=...` 查看最近标注。

## 5) 指标与回放
- `GET /admin/experiments/{id}/metrics` 返回样本数、variant 分组、MAE、Spearman、分布统计。
- `GET /admin/experiments/{id}/runs` 查看最近运行。
- `GET /admin/assessments/{id}/compare?models=v0,v1&experiment_id=...` 生成对比回放输出。

## 6) 离线调参
```bash
python scripts/tune_gsti.py --dsn postgresql+asyncpg://postgres:postgres@localhost:5432/jobshield
```
输出：
- `output/tuning_results.csv`
- `output/best_params.json`

样本不足（<20）会告警，但脚本仍可执行。
