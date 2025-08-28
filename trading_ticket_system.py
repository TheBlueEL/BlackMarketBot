
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
            description="Please select which items you wish to sell.",
            color=0xff6b35
        )
        embed.set_footer(text=f"{self.bot.user.name} - Trading Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_selling_list_embed(self, user, items_list):
        """Create the selling list embed with items"""
        embed = discord.Embed(
            title="💰 Selling Ticket",
            color=0xff6b35
        )
        
        if not items_list:
            embed.description = "Please select which items you wish to sell."
        else:
            # Group items by name (combining dupe and clean)
            grouped_items = {}
            total_value = 0
            
            for item in items_list:
                item_name = item['name']
                if item_name not in grouped_items:
                    grouped_items[item_name] = {'quantity': 0, 'total_value': 0}
                
                grouped_items[item_name]['quantity'] += item['quantity']
                grouped_items[item_name]['total_value'] += item['value'] * item['quantity']
                total_value += item['value'] * item['quantity']
            
            # Calculate Robux rate based on total value
            robux_rate = self.calculate_robux_rate(total_value)
            
            # Create the table
            description = f"```\n{'Item':<50} {'Quantity':<10} {'Price':<15}\n{'-' * 75}\n"
            
            for item_name, data in grouped_items.items():
                quantity = data['quantity']
                value_millions = data['total_value'] / 1_000_000
                robux_price = int(value_millions * robux_rate)
                
                description += f"{item_name:<50} {quantity:<10} {robux_price:,} Robux\n"
            
            total_millions = total_value / 1_000_000
            total_robux = int(total_millions * robux_rate)
            description += f"{'-' * 75}\n"
            description += f"{'TOTAL':<50} {'':<10} {total_robux:,} Robux\n"
            description += "```"
            
            embed.description = description
        
        embed.set_footer(text=f"{self.bot.user.name} - Trading Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    def calculate_robux_rate(self, total_value):
        """Calculate Robux rate based on total value"""
        if total_value < 150_000_000:
            return 80  # 80 robux per million
        elif total_value < 300_000_000:
            return 85  # 85 robux per million
        else:
            return 90  # 90 robux per million

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
                add_reactions=True,
                attach_files=False,
                embed_links=False,
                use_application_commands=True
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
        
        # Create selling embed
        selling_embed = await self.ticket_system.create_selling_embed(interaction.user)
        
        # Create selling form view
        selling_view = SellingFormView(self.ticket_system, self.user_id)
        
        # Update the message with selling embed and form buttons
        await interaction.response.edit_message(embed=selling_embed, view=selling_view)
        
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

class SellingFormView(discord.ui.View):
    def __init__(self, ticket_system, user_id):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = []
    
    @discord.ui.button(label='Add Item', style=discord.ButtonStyle.success, emoji='➕')
    async def add_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return
        
        modal = ItemModal(self, "add")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Remove Item', style=discord.ButtonStyle.danger, emoji='➖')
    async def remove_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return
        
        modal = ItemModal(self, "remove")
        await interaction.response.send_modal(modal)

class ItemModal(discord.ui.Modal):
    def __init__(self, parent_view, action):
        self.parent_view = parent_view
        self.action = action
        title = "Add Item" if action == "add" else "Remove Item"
        super().__init__(title=title)
        
        self.item_name = discord.ui.TextInput(
            label="Item Name",
            placeholder="Enter the item name...",
            required=True,
            max_length=100
        )
        
        self.quantity = discord.ui.TextInput(
            label="Quantity",
            placeholder="1",
            required=False,
            default="1",
            max_length=10
        )
        
        self.status = discord.ui.TextInput(
            label="Status",
            placeholder="Dupe or Clean",
            required=True,
            max_length=10
        )
        
        self.add_item(self.item_name)
        self.add_item(self.quantity)
        self.add_item(self.status)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Validate status
        status = self.status.value.strip().lower()
        if status not in ['dupe', 'clean']:
            await interaction.followup.send("❌ Status must be either 'Dupe' or 'Clean'!", ephemeral=True)
            return
        
        # Validate quantity
        try:
            quantity = int(self.quantity.value.strip()) if self.quantity.value.strip() else 1
            if quantity <= 0:
                await interaction.followup.send("❌ Quantity must be a positive number!", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("❌ Quantity must be a valid number!", ephemeral=True)
            return
        
        # Use le vrai système de stockage
        stockage_system = StockageSystem()
        
        # Trouver l'item comme dans /add_stock
        best_match, duplicates = stockage_system.find_best_match(self.item_name.value.strip(), "None")
        
        if not best_match:
            await interaction.followup.send(f"❌ Item '{self.item_name.value}' not found in database!", ephemeral=True)
            return
        
        if len(duplicates) > 1:
            await interaction.followup.send(f"❌ Multiple items found for '{self.item_name.value}'. Please be more specific with the type!", ephemeral=True)
            return
        
        item_name, item_data = best_match[0], best_match[1]
        
        # Obtenir la valeur selon le statut
        if status == "clean":
            value_key = 'Cash Value'
        else:  # dupe
            value_key = 'Duped Value'
        
        value_str = item_data.get(value_key, 'N/A')
        
        if value_str == 'N/A' or not value_str or value_str == "N/A":
            await interaction.followup.send(f"❌ No {status} value available for '{item_name}'!", ephemeral=True)
            return
        
        # Convertir la valeur en nombre (gérer le format "48 000 000")
        try:
            if isinstance(value_str, str):
                # Enlever tous les espaces et convertir en entier
                clean_value_str = value_str.replace(' ', '').replace(',', '')
                value = int(clean_value_str)
            elif isinstance(value_str, (int, float)):
                value = int(value_str)
            else:
                raise ValueError(f"Type de valeur non supporté: {type(value_str)}")
        except (ValueError, TypeError) as e:
            await interaction.followup.send(f"❌ Invalid {status} value for '{item_name}': {value_str} (Error: {str(e)})", ephemeral=True)
            return
        
        # Nettoyer le nom de l'item (enlever le type entre parenthèses)
        import re
        clean_name = re.sub(r'\s*\([^)]*\)$', '', item_name).strip()
        
        item_entry = {
            'name': clean_name,
            'quantity': quantity,
            'status': status.capitalize(),
            'value': value
        }
        
        if self.action == "add":
            self.parent_view.items_list.append(item_entry)
            action_text = "added to"
        else:  # remove
            # Find and remove the item
            removed = False
            for i, existing_item in enumerate(self.parent_view.items_list):
                if (existing_item['name'] == item_entry['name'] and 
                    existing_item['status'] == item_entry['status']):
                    if existing_item['quantity'] > quantity:
                        existing_item['quantity'] -= quantity
                        removed = True
                        break
                    elif existing_item['quantity'] == quantity:
                        self.parent_view.items_list.pop(i)
                        removed = True
                        break
                    else:
                        await interaction.followup.send(f"❌ Cannot remove {quantity} items. Only {existing_item['quantity']} available!", ephemeral=True)
                        return
            
            if not removed:
                await interaction.followup.send(f"❌ Item '{item_entry['name']}' ({status}) not found in your list!", ephemeral=True)
                return
            
            action_text = "removed from"
        
        # Update the embed
        new_embed = await self.parent_view.ticket_system.create_selling_list_embed(
            interaction.user, 
            self.parent_view.items_list
        )
        
        await interaction.edit_original_response(embed=new_embed, view=self.parent_view)
        await interaction.followup.send(f"✅ {item_entry['name']} x{quantity} ({status}) {action_text} your selling list!", ephemeral=True)

# Import du vrai système de stockage
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from stockage_system import StockageSystem

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
