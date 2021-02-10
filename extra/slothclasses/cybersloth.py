import discord
from discord.ext import commands
from .player import Player
from mysqldb import the_database
from extra.menu import ConfirmSkill
import os
from datetime import datetime

bots_and_commands_channel_id = int(os.getenv('BOTS_AND_COMMANDS_CHANNEL_ID'))

class Cybersloth(Player):

	def __init__(self, client) -> None:
		self.client = client
		# self.bots_txt = await self.client.fetch_channel(bots_and_commands_channel_id)

	@commands.command(aliases=['eb', 'energy', 'boost'])
	@Player.skill_on_cooldown()
	@Player.user_is_class('cybersloth')
	@Player.skill_mark()
	async def hack(self, ctx, target: discord.Member = None) -> None:
		""" A command for Cybersloths. """

		attacker = ctx.author

		if ctx.channel.id != bots_and_commands_channel_id:
			return await ctx.send(f"**{attacker.mention}, you can only use this command in {self.bots_txt.mention}!**")

		if await self.is_user_knocked_out(attacker.id):
			return await ctx.send(f"**{attacker.mention}, you can't use your skill, because you are knocked-out!**")

		if not target:
			return await ctx.send(f"**Please, inform a target member, {attacker.mention}!**")

		if attacker.id == target.id:
			return await ctx.send(f"**{attacker.mention}, you cannot hack yourself!**")

		if target.bot:
			return await ctx.send(f"**{attacker.mention}, you cannot hack a bot!**")

		if not await self.get_user_currency(target.id):
			return await ctx.send(f"**You cannot hack someone who doesn't have an account, {attacker.mention}!**")

		if await self.is_user_protected(target.id):
			return await ctx.send(f"**{attacker.mention}, {target.mention} is protected, you can't hack them!**")

		if await self.is_user_hacked(target.id):
			return await ctx.send(f"**{attacker.mention}, {target.mention} is already hacked!**")


		confirmed = await ConfirmSkill(f"**{attacker.mention}, are you sure you want to hack {target.mention}?**").prompt(ctx)
		if not confirmed:
			return await ctx.send("**Not hacking them, then!**")

		try:
			current_timestamp = await self.get_timestamp()
			# Don't need to store it, since it is forever
			await self.update_user_is_hacked(target.id, 1)
			await self.insert_skill_action(
				user_id=attacker.id, skill_type="hack", skill_timestamp=current_timestamp,
				target_id=target.id, channel_id=ctx.channel.id
			)
			await self.update_user_action_skill_ts(attacker.id, current_timestamp)
			hack_embed = await self.get_hack_embed(
				channel=ctx.channel, perpetrator_id=attacker.id, target_id=target.id)
			msg = await ctx.send(embed=hack_embed)
		except Exception as e:
			print(e)
			return await ctx.send(f"**Something went wrong and your `Hack` skill failed, {attacker.mention}!**")

	@commands.command()
	@Player.skill_two_on_cooldown()
	@Player.user_is_class('cybersloth')
	@Player.skill_mark()
	@Player.not_ready()
	async def wire(self, ctx, target: discord.Member = None) -> None:
		""" Wires someone so if they buy a potion or transfer money to someone, 
		it siphons off up to 35% of the value amount. 
		:param target: The person who you want to wire. """

		pass



	async def check_hacks(self) -> None:

		""" Check on-going hacks and their expiration time. """

		hacks = await self.get_expired_hacks()
		for h in hacks:
			await self.delete_skill_action_by_target_id_and_skill_type(h[3], 'hack')
			await self.update_user_is_hacked(h[3], 0)

			channel = self.bots_txt
		
			await channel.send(
				content=f"<@{h[0]}>",
				embed=discord.Embed(
					description=f"**<@{h[3]}> updated his firewall so <@{h[0]}>'s hacking has no effect anymore! 💻**",
					color=discord.Color.red()))


	async def update_user_is_hacked(self, user_id: int, hacked: int) -> None:
		""" Updates the user's protected state.
		:param user_id: The ID of the member to update. 
		:param hacked: Whether it's gonna be set to true or false. """

		mycursor, db = await the_database()
		await mycursor.execute("UPDATE UserCurrency SET hacked = %s WHERE user_id = %s", (hacked, user_id))
		await db.commit()
		await mycursor.close()


	async def get_hack_embed(self, channel: discord.TextChannel, perpetrator_id: int, target_id: int,) -> discord.Embed:
		""" Makes an embedded message for a hacking skill action.
		:param channel: The context channel.
		:param perpetrator_id: The ID of the perpetrator of the hacking.
		:param target_id: The ID of the target of the hacking. """

		timestamp = await self.get_timestamp()

		hack_embed = discord.Embed(
			title="Someone just got Hacked and lost Control of Everything!",
			timestamp=datetime.utcfromtimestamp(timestamp)
		)
		hack_embed.description=f"**<@{perpetrator_id}> hacked <@{target_id}>!** <a:hackerman:652303204809179161>"
		# hack_embed.description=f"**<@{perpetrator_id}> hacked <@{attacker_id}>!** <a:hackerman:802354539184259082>"
		hack_embed.color=discord.Color.green()

		hack_embed.set_thumbnail(url="https://thelanguagesloth.com/media/sloth_classes/Cybersloth.png")
		hack_embed.set_footer(text=channel.guild, icon_url=channel.guild.icon_url)

		return hack_embed