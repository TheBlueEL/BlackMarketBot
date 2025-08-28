
import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
from datetime import datetime

class TradingTicketSystem:
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'trading_ticket_data.json'
        self.load_data()
    
    def load_data(self):
        """Load trading ticket data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {
                "support_roles": [],
                "ticket_category_id": None,
                "active_tickets": {}
            }
            self.save_data()
    
    def save_data(self):
        """Save trading ticket data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving trading ticket data: {e}")
    
    def get_support_roles(self, guild):
        """Get support role objects from guild"""
        roles = []
        for role_id in self.data.get('support_roles', []):
            try:
                role = guild.get_role(int(role_id))
                if role:
                    roles.append(role)
            except:
                continue
        return roles
    
    async def create_ticket_embed(self):
        """Create the main ticket panel embed"""
        embed = discord.Embed(
            title="🛒 Buying / Selling Ticket",
            description="Welcome to our Jailbreak trading ticket system! We're here to help you buy and sell your valuable items safely and efficiently.\n\nClick the **Create Ticket** button below to get started with your trading journey!",
            color=0x00ff88
        )
        embed.set_footer(text=f"{self.bot.user.name} - Ticket System")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed
    
    async def create_ticket_options_embed(self, user):
        """Create the ticket options embed"""
        embed = discord.Embed(
            title="🎯 Trading / Selling Ticket",
            description=f"Welcome back {user.mention}!\n\nTo continue, please click on one of the two buttons below. Please note that all obtainable items and/or items worth less than 2.5M are not of interest to us and are not available in the item selection choices.\n\nChoose your trading preference:",
            color=0x0099ff
        )
        embed.set_footer(text=f"{self.bot.user.name} - Trading Hub")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed
    
    async def create_selling_embed(self, user):
        """Create the selling ticket embed"""
        embed = discord.Embed(
            title="💰 Selling Ticket",
            description=f"Perfect choice, {user.mention}!\n\nPlease add all the items you wish to sell below. Our team will review your items and get back to you with the best offers.\n\nMake sure to list items worth **2.5M+** for the best trading experience!",
            color=0xff6b35
        )
        embed.set_footer(text=f"{self.bot.user.name} - Selling Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

class TicketPanelView(discord.ui.View):
    def __init__(self, ticket_system):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
    
    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.success, emoji='🎫')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Check if user already has an active ticket
        user_id = str(interaction.user.id)
        if user_id in self.ticket_system.data['active_tickets']:
            ticket_channel_id = self.ticket_system.data['active_tickets'][user_id]
            try:
                ticket_channel = interaction.guild.get_channel(ticket_channel_id)
                if ticket_channel:
                    await interaction.followup.send(f"You already have an active ticket: {ticket_channel.mention}", ephemeral=True)
                    return
                else:
                    # Channel doesn't exist anymore, remove from data
                    del self.ticket_system.data['active_tickets'][user_id]
                    self.ticket_system.save_data()
            except:
                del self.ticket_system.data['active_tickets'][user_id]
                self.ticket_system.save_data()
        
        # Create ticket channel
        guild = interaction.guild
        support_roles = self.ticket_system.get_support_roles(guild)
        
        # Set permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=False,
                add_reactions=False,
                attach_files=False,
                embed_links=False
            ),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        
        # Add support roles
        for role in support_roles:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        
        # Create channel
        channel_name = f"ticket-{interaction.user.name.lower()}-{interaction.user.discriminator}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            reason=f"Trading ticket created by {interaction.user}"
        )
        
        # Save ticket data
        self.ticket_system.data['active_tickets'][user_id] = ticket_channel.id
        self.ticket_system.save_data()
        
        # Send options embed in ticket channel
        options_embed = await self.ticket_system.create_ticket_options_embed(interaction.user)
        view = TicketOptionsView(self.ticket_system, interaction.user.id)
        await ticket_channel.send(embed=options_embed, view=view)
        
        await interaction.followup.send(f"Your ticket has been created! {ticket_channel.mention}", ephemeral=True)

class TicketOptionsView(discord.ui.View):
    def __init__(self, ticket_system, user_id):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
    
    @discord.ui.button(label='Selling', style=discord.ButtonStyle.primary, emoji='💰')
    async def selling_option(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Create selling embed
        selling_embed = await self.ticket_system.create_selling_embed(interaction.user)
        
        # Update the message with selling embed and remove buttons
        await interaction.edit_original_response(embed=selling_embed, view=None)
        
        # Notify support team
        support_roles = self.ticket_system.get_support_roles(interaction.guild)
        if support_roles:
            role_mentions = " ".join([role.mention for role in support_roles])
            await interaction.followup.send(f"🔔 {role_mentions} New selling ticket created by {interaction.user.mention}!")
    
    @discord.ui.button(label='Buying', style=discord.ButtonStyle.secondary, emoji='🛒')
    async def buying_option(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return
        
        await interaction.response.send_message("Buying option will be implemented soon! Please choose Selling for now.", ephemeral=True)

def setup_trading_ticket_system(bot):
    """Setup function to integrate trading ticket system with the bot"""
    ticket_system = TradingTicketSystem(bot)
    
    @bot.tree.command(name="trading_ticket", description="Create a trading ticket panel")
    @app_commands.describe(channel="Channel where to send the ticket panel (optional)")
    async def trading_ticket(interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Command to create trading ticket panel"""
        
        # Check if user has permission (you can modify this check as needed)
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        
        # Create and send ticket panel
        embed = await ticket_system.create_ticket_embed()
        view = TicketPanelView(ticket_system)
        
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Trading ticket panel created in {target_channel.mention}!", ephemeral=True)
    
    return ticket_system
