# -*- coding: utf-8 -*-
# python3.9.7
import json
import os
import time

import discord
from discord.ext import commands


# BOTの設定
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
module_dir = os.path.dirname(__file__)

# secret.pyから呼び出し
TOKEN = os.environ['DISCORD_BOT_TOKEN']
create_ch = int(os.environ['CHANNEL_ID'])
create_cat = int(os.environ['CATEGORY_ID'])
role_id = int(os.environ['ROLE_ID'])


# 起動時の動作
@bot.event
async def on_ready():
    print('------')
    print(f'{bot.user.name}')
    print(f'{bot.user.id}')
    print('------')
    await bot.change_presence(activity=discord.Game(name='原神', type=1))


# メイン
@bot.event
async def on_voice_state_update(member, before, after):
    vase = bot.get_channel(create_ch)  # 塵歌壺に入るチャンネル
    vase_cat = bot.get_channel(create_cat)
    guild = member.guild  # サーバー情報
    role = guild.get_role(role_id)  # 付与するロール情報取得
    mn = member.name.replace(" ", "").lower()  # メンバー名 小文字、空白なし

    # JSONを辞書化
    json_path = os.path.join(module_dir, 'create.json')
    json_open = open(json_path, 'r', encoding="utf-8_sig")
    json_data = json.load(json_open)

    if before.channel is not after.channel:  # 入退室でのみ反応
        ownerFlg = False

        # 退室時
        if before.channel is not None:
            for owned in json_data.keys():
                if before.channel.id == json_data[owned]["voice_ch_id"]:
                    print("退室")
                    await member.remove_roles(role)
                    re_role = discord.utils.get(guild.roles, name=owned)
                    await member.remove_roles(re_role)

                    # VCがbotだけの場合True
                    botFlg = True
                    for mem in before.channel.members:
                        if not mem.bot:
                            botFlg = False

                    # botだけもしくはvcに人がいない場合、削除
                    if botFlg or len(before.channel.members) == 0:
                        vc_id = discord.utils.get(guild.voice_channels, id=json_data[owned]["voice_ch_id"])
                        txt_id = discord.utils.get(guild.text_channels, id=json_data[owned]["text_ch_id"])
                        await vc_id.delete()
                        await txt_id.delete()
                        await re_role.delete()
                        json_data.pop(owned)  # jsonからオーナー情報を削除
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=4, ensure_ascii=False)
                        break

        owner = [owner for owner in json_data.keys()]

        if mn not in owner:
            # 自動作成チャンネルにユーザー入室時処理
            # カテゴリーで重複チェック＆作成
            if after.channel == vase:
                print("チャンネル自動生成")
                # ボイスチャンネルを作成
                perms = discord.Permissions(manage_channels=True)
                mv_ch = await guild.create_voice_channel(mn, category=vase_cat)
                await guild.create_role(name=mn, permissions=perms)
                time.sleep(0.1)
                join_role = [r for r in guild.roles if r.name == mn]
                print(join_role)
                # プライベートチャンネルの設定
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(read_messages=True),
                    join_role[0]: discord.PermissionOverwrite(read_messages=True)
                }
                # プライベートチャンネルの作成
                txt_ch = await guild.create_text_channel(mn, overwrites=overwrites, category=vase_cat)
                # 各チャンネルのIDを取得
                vc_ch = discord.utils.get(guild.voice_channels, name=mn)
                join_role = [r for r in guild.roles if r.name == mn]
                await member.add_roles(join_role[0])

                # 取得したチャンネルIDをjsonに書き出し
                ch_json = {mn: {"voice_ch_id": vc_ch.id, "text_ch_id": txt_ch.id}}
                json_data.update(ch_json)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)
                time.sleep(0.5)
                ownerFlg = True
                await member.move_to(mv_ch)

            # オーナー以外の退室時
            '''
            elif before.channel is not None:
                for owned in json_data.keys():
                    if before.channel.id == json_data[owned]["voice_ch_id"]:
                        print("オーナー以外退室")
                        await member.remove_roles(role)
                        re_role = discord.utils.get(guild.roles, name=owned)
                        await member.remove_roles(re_role)
            '''

            # オーナー以外の入室
            print(f"after_ch {after.channel}")
            for owned in json_data.keys():
                if after.channel is not None and after.channel.id == json_data[owned]["voice_ch_id"] and not ownerFlg:
                    print("オーナー以外入室")
                    msg_path = os.path.join(module_dir, 'message.json')
                    msg_open = open(msg_path, 'r', encoding="utf-8_sig")
                    msg_data = json.load(msg_open)
                    guest_message = msg_data["guest_message"]
                    txt_own = discord.utils.get(guild.text_channels, id=json_data[owned]["text_ch_id"])
                    await member.add_roles(role)
                    re_role = discord.utils.get(guild.roles, name=owned)
                    await member.add_roles(re_role)
                    await txt_own.send(f"<@{member.id}> {guest_message}")

        # オーナーの処理
        else:
            owner_list = [ow for ow in json_data.keys()]
            if mn in owner_list:
                json_path = os.path.join(module_dir, 'create.json')
                json_open = open(json_path, 'r', encoding="utf-8_sig")
                json_data = json.load(json_open)
                vc_id = discord.utils.get(guild.voice_channels, id=json_data[mn]["voice_ch_id"])
                txt_id = discord.utils.get(guild.text_channels, id=json_data[mn]["text_ch_id"])

                # オーナー退室
                '''
                if before.channel is not None:
                    if before.channel.id == vc_id.id:
                        print("オーナー退室")
                        # オーナーカテゴリー内のチャンネルを削除
                        await vc_id.delete()
                        await txt_id.delete()
                        await member.remove_roles(role)
                        for jr in guild.roles:
                            if jr.name == mn:
                                await jr.delete()
                        json_data.pop(mn)  # jsonからオーナー情報を削除
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=4, ensure_ascii=False)
                        return
                '''

                # オーナー入室
                if after.channel is not None:
                    if after.channel.id == vc_id.id:
                        print("オーナー入室")
                        txt_id = discord.utils.get(guild.text_channels, id=json_data[mn]["text_ch_id"])
                        msg_path = os.path.join(module_dir, 'message.json')
                        msg_open = open(msg_path, 'r', encoding="utf-8_sig")
                        msg_data = json.load(msg_open)
                        welcome_message = msg_data["welcome_message"]
                        await txt_id.send(welcome_message)
                        await member.add_roles(role)

bot.run(TOKEN)
