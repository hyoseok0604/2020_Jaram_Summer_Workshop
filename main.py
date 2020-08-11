import asyncio

import discord
import requests

from bs4 import BeautifulSoup

client = discord.Client()

base_url_cf = "https://codeforces.com/api/"
base_url_boj = "https://www.acmicpc.net/"


class Vote:
    before_start = 0
    voting = 1
    end = 2

    def __init__(self, title, by):
        self.counts = []
        self.title = title
        self.choices = []
        self.by = by
        self.status = 0

    def start(self):
        for _ in self.choices:
            self.counts.append([])


votes = []


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game("장효석 Bot"))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == '#hyoseok':
        await message.channel.send("Hello world")

    if message.content.startswith('#cf'):
        args = message.content.split(' ')
        if args[1] == 'user':
            if args[2] == 'info':
                loop = asyncio.get_event_loop()
                method = "user.info?"
                future = loop.run_in_executor(None, requests.get, base_url_cf + method + "handles=" + args[3])
                response = await future
                result = response.json()

                if result['status'] != 'OK':
                    await message.channel.send("Error")
                else:
                    result = result['result'][0]

                    embed = discord.Embed(title=args[3], url="https://codeforces.com/profile/" + args[3],
                                          description="Codeforces User Info")
                    embed.add_field(name='Handle', value=args[3])

                    fields = [['country', 'Country'],
                              ['city', 'City'],
                              ['organization', 'Organization'],
                              ['rank', 'Rank'],
                              ['rating', 'Rating'],
                              ['maxRank', 'Max Rank'],
                              ['maxRating', 'Max Rating']]

                    for field in fields:
                        if field[0] in result.keys():
                            if field[0] in ['rank', 'maxRank']:
                                embed.add_field(name=field[1], value=str(result[field[0]]).capitalize(), inline=False)
                            else:
                                embed.add_field(name=field[1], value=result[field[0]], inline=False)
                    await message.channel.send(embed=embed)
        elif args[1] == 'help':
            pass

    if message.content.startswith('#boj'):
        args = message.content.split(' ')
        if args[1] == 'user':
            if args[2] == 'info':
                loop = asyncio.get_event_loop()
                future = loop.run_in_executor(None, requests.get, 'https://www.acmicpc.net/user/' + args[3])
                response = await future
                bs = BeautifulSoup(response.text, "html.parser")
                result = dict()
                for line in bs.find('table', {'id': 'statics'}).find_all('tr'):
                    k = line.find('th').text
                    values = []
                    deep_search(line.find('td'), values)

                    result[k] = ', '.join(values)

                embed = discord.Embed(title=args[3], url='https://www.acmicpc.net/user/' + args[3],
                                      description="Baekjoon Online Judge User Info")
                embed.add_field(name='Name', value=args[3])

                for k, v in result.items():
                    embed.add_field(name=k, value=v, inline=False)

                await message.channel.send(embed=embed)
        elif args[1] == 'help':
            pass

    if message.content.startswith('#vote'):
        args = message.content.split(' ')
        # vote [make|edit|remove|start|end|list|info]

        if args[1] == 'make':  # #vote make [제목] "투표 생성"
            title = str(message.content).replace('#vote make ', '')
            votes.append(Vote(title=title, by=message.author.name + '#' + message.author.discriminator,))
            await message.channel.send("투표가 추가되었습니다")
        elif args[1] == 'list':  # #vote list "투표 리스트"
            idx = 1
            if len(votes) == 0:
                embed = discord.Embed()
                embed.add_field(name="오류", value="등록된 투표가 존재하지 않습니다.")
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed()
                for vote in votes:
                    text = str(idx) + ". " + vote.title + " / " + vote.by + " / "
                    if vote.status == 0:
                        text += "투표 시작 전"
                    elif vote.status == 1:
                        text += "투표 중"
                    elif vote.status == 2:
                        text += "투표 종료"
                    embed.add_field(name="제목", value=text, inline=False)
                await message.channel.send(embed=embed)
        elif args[1] == 'remove':  # #vote remove [index] "투표 삭제"
            vote = votes[int(args[2])-1]
            if vote.by != message.author.name + '#' + message.author.discriminator:
                await message.channel.send("투표를 생성한 유저가 아닙니다")
            else:
                await message.channel.send(args[2] + "번째 투표가 제거되었습니다")
                votes.remove(vote)
        elif args[1] == 'clear':  # #vote clear "투표 전체 삭제"
            votes.clear()
        elif args[1] == 'start':  # #vote start [index] "투표 시작"
            vote = votes[int(args[2])-1]
            if vote.by != message.author.name + '#' + message.author.discriminator:
                await message.channel.send("투표를 생성한 유저가 아닙니다")
            else:
                await message.channel.send(args[2] + "번째 투표가 시작되었습니다")
                vote.status = Vote.voting
                vote.start()
        elif args[1] == 'end':  # #vote start [index] "투표 종료"
            vote = votes[int(args[2])-1]
            if vote.by != message.author.name + '#' + message.author.discriminator:
                await message.channel.send("투표를 생성한 유저가 아닙니다")
            else:
                await message.channel.send(args[2] + "번째 투표가 종료되었습니다")
                vote.status = Vote.end
        elif args[1] == 'edit':
            vote = votes[int(args[2])-1]
            if vote.by != message.author.name + '#' + message.author.discriminator:
                await message.channel.send("투표를 생성한 유저가 아닙니다")
            elif vote.status != 0:
                await message.channel.send("투표 시작 전에만 항목을 변경할 수 있습니다")
            else:
                if args[3] == 'add':  # #vote edit [index] add [항목] "투표 항목 추가"
                    choice = str(message.content).replace('#vote edit ' + args[2] + ' add ', '')
                    vote.choices.append(choice)
                    await message.channel.send("항목이 추가되었습니다")
                if args[3] == 'edit':  # #vote edit [index] edit [index] [항목] "투표 항목 변경"
                    new_choice = str(message.content).replace('#vote edit ' + args[2] + ' edit ' + args[4] + ' ', '')
                    vote.choices[int(args[4]) - 1] = new_choice
                    await message.channel.send("항목이 변경되었습니다")
                if args[3] == 'remove':  # #vote edit [index] remove [index] "투표 항목 제거"
                    choice = vote.choice[int(args[3]) - 1]
                    vote.choices.remove(choice)
                    await message.channel.send("항목이 제거되었습니다")
        elif args[1] == 'info':
            vote = votes[int(args[2]) - 1]
            embed = discord.Embed()
            embed.add_field(name="제목", value=vote.title, inline=False)
            embed.add_field(name="만든 사람", value=vote.by, inline=False)
            s = ""
            if vote.status == 0:
                s += "투표 시작 전"
            elif vote.status == 1:
                s += "투표 중"
            elif vote.status == 2:
                s += "투표 종료"
            embed.add_field(name="상태", value=s, inline=False)
            idx = 1
            for choice in vote.choices:
                val = choice
                if vote.status != 0:
                    val += " / " + str(len(vote.counts[idx-1])) + "표"
                embed.add_field(name="항목" + str(idx), value=val, inline=False)
                idx += 1
            await message.channel.send(embed=embed)
        else:
            vote = votes[int(args[1]) - 1]
            if vote.status != 1:
                await message.channel.send("투표가 진행중이 아닙니다")
            else:
                for count in vote.counts:
                    if message.author.name + '#' + message.author.discriminator in count:
                        count.remove(message.author.name + '#' + message.author.discriminator)

                vote.counts[int(args[2]) - 1].append(message.author.name + '#' + message.author.discriminator)

                await message.channel.send(vote.title + " 투표의 " + vote.choices[int(args[2]) - 1] + " 항목에 투표되었습니다")


def deep_search(bs, dest):
    direct_child = bs.find_all(recursive=False)
    if len(direct_child) == 0:
        return dest.append(bs.text.strip())
    else:
        for child in direct_child:
            deep_search(child, dest)


client.run('NzQyNjEzOTU5MTk4Mzc2MDE3.XzIrJA.ba9HYbHYTQeyCWdqFTIV2p5HU6o')
