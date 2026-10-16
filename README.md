# 原神角色生日与周年庆日历

已生成的日历：[docs/genshin-birthdays.ics](docs/genshin-birthdays.ics)。文件包含 120 位有公开生日资料的角色、每年 9 月 28 日的原神周年庆、前一天 20:00 提醒，以及上周五 20:00 的下周生日汇总。日期按北京时间（Asia/Shanghai）生成；旅行者生日由玩家自行设置，因此未列入。

## 使用

- **立即导入：**在 Apple 设备上打开 `.ics` 文件，选择导入到日历。这份副本不会自动更新。
- **自动更新：**打开[日历订阅页](https://peterlab-embeded.github.io/genshin-birthday-calendar/)，点“订阅 Apple 日历”。也可在 Apple 日历的“日历 → 添加日历 → 添加订阅日历”中粘贴 `https://peterlab-embeded.github.io/genshin-birthday-calendar/genshin-birthdays.ics`。订阅更新的显示时间取决于 Apple 日历的刷新。
- 请在设备的“设置 → 通知 → 日历”开启通知。订阅日历是否显示事件内的提醒也取决于 Apple 系统设置，首次订阅后请用一个近期提醒验证。

## 自动更新

公开仓库的 [GitHub Actions 工作流](https://github.com/PeterLab-embeded/genshin-birthday-calendar/actions) 每天北京时间约 08:15 扫描公开生日索引，重建 `.ics` 并发布到 GitHub Pages。GitHub 的计划任务可能延迟。新角色先以英文名称进入日历；可在 `names_zh.json` 补中文名。

日历当前采用公开的 [Fan Support 生日索引](https://fansupport.joelin.cc/en/group/genshin-impact/) 并与 [Genshin Impact Wiki 生日表](https://genshin-impact.fandom.com/wiki/Birthday) 交叉核对。来源会变动，`scan-report.json` 记录每次扫描新增与删除/改期项目；抓取异常会让工作流失败，保留上一次已发布日历。原神于 [2020 年 9 月 28 日全球上线](https://genshin.hoyoverse.com/en/news/detail/5284)。

## 本地更新

```powershell
python build_calendar.py --refresh
```

离线时直接运行 `python build_calendar.py`，用已保存的数据重建。生日提醒逐年生成到当前年份后 10 年；每日更新会延长这个范围。2 月 29 日生日仅在闰年显示，当年前一天提醒为 2 月 28 日 20:00。
