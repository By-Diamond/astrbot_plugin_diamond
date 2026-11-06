# 钻石插件

## 今日老婆

群聊发送“今日老婆”或“换老婆”，每位用户在每个群每天共有两次抽选机会。两个指令共用次数，每次成功抽选消耗一次，北京时间零点重置。第二次抽选提示“渣男，再换你今天就没老婆了！”，并在有其他成员时避免重复上次结果。

回复依次为：@触发人、提示文字、群友头像、群友昵称(QQ号)。次数耗尽后，两个指令均只回复“@触发人渣男！你今天没老婆了！”。获取群成员失败不扣次数。

次数按平台、群和用户隔离，保存至插件目录的 wife_data.json。旧版仅按用户保存的记录保留，但不计入新版群内次数；升级当天每个群从两次开始。

## 今日图图

“今日图图”和“换图图”替代旧指令“今日萝莉”和“换萝莉”。每位用户在每个群每天两次，图片获取失败不扣次数。记录保存至 picture_data.json。

在 AstrBot 插件配置中设置：

- picture_source：auto、local 或 external。auto 优先本地，本地无图时使用外部接口。
- picture_local_dir：默认 images，即插件目录下的 images 文件夹。支持 jpg、jpeg、png、gif、webp。也可以填写容器内可见的绝对路径。
- picture_external_url：默认沿用旧图库 https://api.yppp.net/pc.php?return=json 。支持返回图片，或返回包含图片 HTTP(S) 地址的 JSON。留空可禁用外部图库。
- picture_external_json_field：JSON 图片地址字段，默认 acgurl，支持 data.url 等路径。

本地目录和外部接口均未配置时，发送明确提示。旧版 loli_data.json 保留，不再使用。图库内容由管理员提供。
