import datetime
import logging
import random

from distee.client import Client
from distee.components import ActionRow, Button, Modal, TextInput
from distee.enums import TextInputType, ButtonStyle, Event
from distee.flags import Intents
from distee.guild import Member
from distee.interaction import Interaction
import json
import os.path

from distee.message import Message

with open('config.json') as conf_file:
    cfg = json.load(conf_file)

logging.basicConfig(level=logging.INFO)

client = Client()
client.build_user_cache = False
client.build_member_cache = False
intents = Intents().set(['GUILDS', 'DIRECT_MESSAGES'])


cache = {}
cooldown = {}

colors = [
    0x434B4D,
    0xB32821,
    0xC6A664,
    0x781F19,
    0xBEBD7F,
    0xA2231D,
    0x343E40,
    0xD84B20,
    0xFFA420,
    0x287233
]

c_success = 0x287233
c_fail = 0xA2231D


def load():
    if os.path.isfile('storage.json'):
        with open('storage.json', 'r') as fi:
            dat = json.load(fi)
        global cache, cooldown
        cache = dat['cache']
        cooldown = dat['cooldown']


def safe():
    dat = {
        'cache': cache,
        'cooldown': cooldown
    }
    with open('storage.json', 'w') as fi:
        json.dump(dat, fi)


@client.event(Event.MESSAGE_SEND)
async def on_message(msg: Message):
    if msg.author_id.id == client.user.id:
        return
    global cache
    if not isinstance(msg.author, Member):
        if msg.content.strip().lower() != 'apply':
            return
        if cooldown.get(str(msg.author_id.id)) is not None and \
                cooldown.get(str(msg.author_id.id)) > datetime.datetime.utcnow().timestamp():
            cd = cooldown.get(str(msg.author_id.id))
            await msg.author.send(embeds=[{'description': f'You already submitted a application recently.\n'
                                                          f'Please wait till <t:{int(cd)}> before you reapply',
                                           'color': c_fail}])
            return
        if cache.get(msg.author_id.id) is None:
            embed = {
                'description': 'We are not always looking for mods. However, when we are, we will look through '
                               'these responses. In the event that you are chosen or we want to discuss your '
                               'application more, we will contact you. Pinging mods to ask about your application or '
                               'asking them when you see them in #general will not help your chances and could result '
                               'in us deleting your application and no longer considering you for a moderator position.'
                               '\n\n**If you understand the above message, please click the button below to start**'
            }
            await msg.author.send(embeds=[embed],
                                  components=[ActionRow([Button(
                                     'btn_modal1',
                                     label='I understand, lets start!'
                                  )])])
            cache[msg.author_id.id] = {}


@client.interaction_handler('btn_modal1')
async def send_modal_stage_1(inter: Interaction):
    modal = Modal('stage_2_trigger',
                  'About you',
                  [ActionRow([
                      TextInput('age', 'What is your age?', max_length=3)
                  ]), ActionRow([
                      TextInput('timezone', 'What is your timezone?',
                                placeholder='examples: UTC+2 or EST', max_length=30)
                  ])])
    await inter.send_modal(modal)


@client.interaction_handler('stage_2_trigger')
async def stage_2(inter: Interaction):
    global cache
    cache[inter.user.id] = {
        'age': inter.data.components['age']['value'],
        'timezone': inter.data.components['timezone']['value']
    }
    await inter.message.delete()
    await inter.send(embeds=[{
        'description': 'So far so good!\n'
                       'The next set of questions are about your relationship with Spectrum and your current thoughts '
                       'on it'
    }], components=[ActionRow([Button(
        'btn_modal2',
        label='Ok lets go!'
    )])])


@client.interaction_handler('btn_modal2')
async def send_modal_stage_2(inter: Interaction):
    modal = Modal('stage_3_trigger',
                  'Relationship to Spectrum',
                  [ActionRow([
                      TextInput('thoughts',
                                'Thoughts on Spectrum?',
                                placeholder='What are your thoughts on Spectrum as a server?',
                                style=TextInputType.PARAGRAPH)
                  ]), ActionRow([
                      TextInput('change',
                                'What would you change about the server?',
                                placeholder='If you could change one thing about Spectrum, what would it be?',
                                style=TextInputType.PARAGRAPH)
                  ])
                  ])
    await inter.send_modal(modal)


@client.interaction_handler('stage_3_trigger')
async def stage_3(inter: Interaction):
    global cache
    thoughts = inter.data.components['thoughts']['value']
    change = inter.data.components['change']['value']
    cache[inter.user.id]['thoughts'] = thoughts
    cache[inter.user.id]['change'] = change
    await inter.message.delete()
    await inter.send(embeds=[{
        'description': 'These next questions are about your thoughts on the current mod team and why you want to join '
                       'them.'
    }], components=[ActionRow([Button(
        'btn_modal3', label='Show me what you got!'
    )])])


@client.interaction_handler('btn_modal3')
async def send_stage_3_modal(inter: Interaction):
    modal = Modal('stage_4_trigger',
                  'Relationship to Spectrum Mod Team',
                  [
                      ActionRow([TextInput(
                          'why_join',
                          'Why do you want to join the mod team?',
                          placeholder='Why do you want to join the mod team?',
                          style=TextInputType.PARAGRAPH
                      )]),
                      ActionRow([TextInput(
                          'why_good_fit',
                          'Why are you a good fit?',
                          placeholder='What do you think makes you a good fit for mod?',
                          style=TextInputType.PARAGRAPH
                      )]),
                      ActionRow([TextInput(
                          'experience',
                          'Moderation experience? Please list.',
                          placeholder='Do you have any experience moderating? If so, what?',
                          style=TextInputType.PARAGRAPH
                      )])
                  ])
    await inter.send_modal(modal)


scenarios = [
    'Someone gets an automated strike from the bot for typing a slur in #general and then starts to complain '
    'about it in #general.',
    'You see another mod post a clearly NSFW meme in #memes.',
    'A longstanding active user misgenders a mod.',
    'Someone opens a ticket to report a user in the server messaging creepy, NSFW things to minors.',
    'The mods make a decision that you heavily disagree with.'
]


@client.interaction_handler('stage_4_trigger')
async def stage_4(inter: Interaction):
    global cache
    current_scenario = cache[inter.user.id].get('current_scenario', 0)
    if current_scenario == 0:
        cache[inter.user.id]['why_join'] = inter.data.components['why_join']['value']
        cache[inter.user.id]['why_good_fit'] = inter.data.components['why_good_fit']['value']
        cache[inter.user.id]['experience'] = inter.data.components['experience']['value']
    cache[inter.user.id]['current_scenario'] = current_scenario + 1
    # store if triggered from correct modal
    if current_scenario > 0:
        cache[inter.user.id][f'scenario_{current_scenario}'] = inter.data.components['answer']['value']
    await inter.message.delete()
    await inter.send(embeds=[{
                         'title': 'Scenarios and Questions about the Server',
                         'description': f'**__Scenario {current_scenario+1}:__**\n'
                                        f'{scenarios[current_scenario]}\n\n'
                                        f'What would you do?'
                     }], components=[ActionRow([Button('btn_modal4', label='I can answer that!')])])


@client.interaction_handler('btn_modal4')
async def send_stage_4_modal(inter: Interaction):
    current_scenario = cache[inter.user.id].get('current_scenario', 0)
    modal = Modal('stage_4_trigger' if current_scenario < len(scenarios) else 'stage_5_trigger',
                  'Scenarios about the Server',
                  [ActionRow([TextInput(
                      'answer', f'Scenario {current_scenario}', style=TextInputType.PARAGRAPH,
                      placeholder='What would you do?'
                  )])])
    await inter.send_modal(modal)
    pass


@client.interaction_handler('stage_5_trigger')
async def stage_5(inter: Interaction):
    global cache
    cache[inter.user.id][f'scenario_{len(scenarios)}'] = inter.data.components['answer']['value']
    await inter.message.delete()
    await inter.send(embeds=[{
                         'description': 'Are there any rules that you think need to be changed? '
                                        'How would you change them?'
                     }],
                     components=[ActionRow([Button(
                         'btn_modal5', label='I got the answer to that!'
                     )])])


@client.interaction_handler('btn_modal5')
async def send_stage_5_modal(inter: Interaction):
    await inter.send_modal(Modal(
        'stage_6_trigger',
        'Question about the Server',
        [ActionRow([TextInput(
            'rules_ideas',
            'Any rules that need to be changed? How?',
            style=TextInputType.PARAGRAPH
        )])]
    ))


@client.interaction_handler('stage_6_trigger')
async def stage_6(inter: Interaction):
    global cache
    cache[inter.user.id]['rules_ideas'] = inter.data.components['rules_ideas']['value']
    await inter.message.delete()
    await inter.send(embeds=[{
                         'title': 'Final Thoughts',
                         'description': 'Is there anything else you might want us to know?'
                     }], components=[ActionRow([
                            Button('btn_final_thoughts',
                                   label='I have some something to tell'),
                            Button('to_final_overview',
                                   label='No, I have nothing to say')
                        ])])


@client.interaction_handler('btn_final_thoughts')
async def send_final_thoughts(inter: Interaction):
    await inter.send_modal(Modal(
        'to_final_overview',
        'Final Thoughts',
        [ActionRow([TextInput(
            'final_thoughts',
            'Anything else you might want us to know',
            style=TextInputType.PARAGRAPH
        )])]
    ))


def get_embeds(inter, header=False):
    answers = cache[inter.user.id]
    parts = list()
    if header:
        parts.append('Please check if everything looks alright to you:\n\n')
    parts.append(f'**__About you__**\n'
                 f'**Username:** {inter.user.username}#{inter.user.discriminator}\n'
                 f'**User ID:** {inter.user.id}\n'
                 f'**Age:** {answers["age"]}\n'
                 f'**Timezone:** {answers["timezone"]}\n\n')
    parts.append(f'**__Relationship to Spectrum__**\n'
                 f'**Thoughts on Spectrum:**\n{answers["thoughts"]}\n'
                 f'**What you would change about the server:**\n{answers["change"]}\n\n')
    parts.append(f'**__Relationship to Spectrum Mod Team__**\n'
                 f'**Why you want to join the mod team:**\n{answers["why_join"]}\n'
                 f'**Why you are a good fit:**\n{answers["why_good_fit"]}\n'
                 f'**Moderation experience:**\n{answers["experience"]}\n\n')
    parts.append(f'**__Scenarios__**\n')
    for idx in range(len(scenarios)):
        parts.append(f'**Scenario {idx + 1}:**\n**Q:** {scenarios[idx]}\n**A:** {answers[f"scenario_{idx + 1}"]}\n\n')
    parts.append(f'**__Rules that need to be changed__**\n'
                 f'{answers["rules_ideas"]}\n\n')
    if answers['final_thoughts'] is not None:
        parts.append(f'**__Final thoughts__**\n{answers["final_thoughts"]}')
    embeds = []
    part = ''
    for p in parts:
        if len(part + p) > 4000:
            embeds.append({'description': part})
            part = p
        else:
            part += p
    if len(part) > 0:
        embeds.append({'description': part})
    return embeds


@client.interaction_handler('to_final_overview')
async def final_overview(inter: Interaction):
    await inter.defer_message_edit()
    global cache
    await inter.message.delete()
    cache[inter.user.id]['final_thoughts'] = inter.data.components['final_thoughts']['value'] \
        if inter.data.components is not None else None
    embeds = get_embeds(inter, header=True)
    _msg_ids = []
    comps = [ActionRow([
                 Button(
                     'btn_send',
                     label='Looks good, lets send',
                     style=ButtonStyle.SUCCESS
                 ),
                 Button(
                     'btn_modal1',
                     label='Something is wrong, lets try again',
                     style=ButtonStyle.DANGER
                 )
             ])]
    for eidx in range(len(embeds)):
        _msg = await inter.user.send(embeds=[embeds[eidx]],
                                     components=comps if eidx == len(embeds) - 1 else None)
        _msg_ids.append(_msg)
    cache[inter.user.id]['_msg'] = _msg_ids


@client.interaction_handler('btn_send')
async def finalize(inter: Interaction):
    global cache, cooldown
    await inter.defer_send()
    embeds = get_embeds(inter)
    g = client.get_guild(cfg['sid'])
    channel = g.get_channel(cfg['cid'])
    first = True
    color = random.choice(colors)
    for e in embeds:
        e['color'] = color
        await channel.send(embeds=[e],
                           content=f'New mod application by <@{inter.user.id}>' if first else None)
        first = False
    for _msg_id in cache[inter.user.id]['_msg']:
        await _msg_id.delete()
    await inter.send_followup(embeds=[{
        'description': 'Your application was successfully send to the mod team!',
        'color': c_success
    }])
    cache.pop(inter.user.id, None)
    cooldown[str(inter.user.id)] = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).timestamp()


load()

try:
    client.run(cfg['token'], intents=intents)
finally:
    safe()
