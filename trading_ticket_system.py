
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
            title="<:CardLOGO:1410734196883853342> Buying / Selling Ticket",
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
            title="<:CardLOGO:1410734196883853342> Buying / Selling Ticket",
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
            title="<:SellingLOGO:1410730163607437344> Selling Ticket",
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
            title="<:SellingLOGO:1410730163607437344> Selling Ticket",
            color=0xff6b35
        )

        if not items_list:
            embed.description = "Please select which items you wish to sell."
        else:
            # Group items by name and type, keeping status for calculations
            grouped_items = {}
            total_value = 0

            for item in items_list:
                key = f"{item['name']} ({item['type']})"
                if key not in grouped_items:
                    grouped_items[key] = {'quantity': 0, 'total_value': 0, 'status': item['status']}

                grouped_items[key]['quantity'] += item['quantity']
                grouped_items[key]['total_value'] += item['value'] * item['quantity']
                total_value += item['value'] * item['quantity']

            # Calculate Robux rate based on total value in millions
            total_millions = total_value / 1_000_000
            robux_rate = self.calculate_robux_rate(total_millions)

            # Create column headers
            items_column = []
            quantities_column = []
            prices_column = []

            # Add each item to the columns
            for item_name, data in grouped_items.items():
                quantity = data['quantity']
                value_millions = data['total_value'] / 1_000_000
                robux_price = int(value_millions * robux_rate)

                items_column.append(item_name)
                quantities_column.append(str(quantity))
                prices_column.append(f"{robux_price:,} <:RobuxLOGO:1410727587134701639>")

            # Add total row
            total_robux = int(total_millions * robux_rate)

            items_column.append("**TOTAL**")
            quantities_column.append("---")
            prices_column.append(f"**{total_robux:,} <:RobuxLOGO:1410727587134701639> (HORS TAXE)**")

            # Create the three fields as columns
            embed.add_field(
                name="<:ItemLOGO:1410730965277474977> Item",
                value="\n".join(items_column),
                inline=True
            )

            embed.add_field(
                name="<:QuantityLOGO:1410730638851444756> Quantity",
                value="\n".join(quantities_column),
                inline=True
            )

            embed.add_field(
                name="<:RobuxLOGO:1410727587134701639> Price",
                value="\n".join(prices_column),
                inline=True
            )

        embed.set_footer(text=f"{self.bot.user.name} - Trading Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_payment_method_embed(self, user, items_list):
        """Create the payment method selection embed"""
        embed = discord.Embed(
            title="<:SellingLOGO:1410730163607437344> Selling Ticket",
            color=0xff6b35
        )
        
        # Calculate total value and robux
        total_value = sum(item['value'] * item['quantity'] for item in items_list)
        total_millions = total_value / 1_000_000
        robux_rate = self.calculate_robux_rate(total_millions)
        total_robux = int(total_millions * robux_rate)
        
        # Calculate tax (30%)
        total_with_tax = int(total_robux * 0.70)
        
        # Create description with items summary
        description_lines = ["You wish to sell all these items:\n"]
        
        # Group items for display
        grouped_items = {}
        for item in items_list:
            key = f"{item['name']} ({item['type']}) ({item['status']})"
            if key not in grouped_items:
                grouped_items[key] = {'quantity': 0, 'total_value': 0}
            
            grouped_items[key]['quantity'] += item['quantity']
            grouped_items[key]['total_value'] += item['value'] * item['quantity']
        
        for item_name, data in grouped_items.items():
            quantity = data['quantity']
            value_millions = data['total_value'] / 1_000_000
            robux_price = int(value_millions * robux_rate)
            
            if quantity == 1:
                description_lines.append(f"• 1x {item_name} {robux_price:,} <:RobuxLOGO:1410727587134701639>")
            else:
                per_item_price = robux_price // quantity
                description_lines.append(f"• {quantity}x {item_name} {robux_price:,} <:RobuxLOGO:1410727587134701639> ({per_item_price:,} robux x{quantity})")
        
        description_lines.append(f"\nFor a total of {total_robux:,} <:RobuxLOGO:1410727587134701639> (Hors Taxe)")
        description_lines.append(f"**__The amount with TAX included is {total_with_tax:,} <:RobuxLOGO:1410727587134701639>__**")
        description_lines.append("\nChoose the method you want to receive your payment.")
        description_lines.append("-# The client will always have to pay first, you have access to our vouch salon right here: <#1312591100971843676>")
        
        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"{self.bot.user.name} - Trading Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_information_embed(self, user):
        """Create the information embed explaining payment methods"""
        embed = discord.Embed(
            title="<:SellingLOGO:1410730163607437344> Selling Ticket",
            color=0xff6b35
        )
        
        description_lines = [
            "**GamePass Method**",
            'The "**GamePass Method**" consists of **creating a Gamepass** on an experience where you can set the price of the amount we will have to pay. This payment is made instantly depending on the availability of our teams.',
            "",
            "**Group Donation Method**",
            'The "**Group Donation Method**" consists of joining our Roblox group in order to receive, after a delay of 2 weeks, implemented by Roblox, your transaction.'
        ]
        
        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"{self.bot.user.name} - Trading Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_gamepass_result_embed(self, user, experience_url):
        """Create embed showing gamepass creation link"""
        embed = discord.Embed(
            title="<:SellingLOGO:1410730163607437344> Selling Ticket",
            description=f"Please use this link to create your GamePass:\n\n [{user}'s GamePass]({experience_url})",
            color=0x00ff00
        )
        embed.set_footer(text=f"{self.bot.user.name} - Trading Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    def calculate_robux_rate(self, total_millions):
        """Calculate Robux rate based on total value in millions"""
        if total_millions < 150:
            return 80  # 80 robux per million
        elif total_millions < 300:
            return 85  # 85 robux per million
        else:
            return 90  # 90 robux per million

    async def create_error_embed(self, title, description):
        """Create error embed for various error messages"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=0xff0000
        )
        embed.set_footer(text=f"{self.bot.user.name} - Trading Department")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

class TicketPanelView(discord.ui.View):
    def __init__(self, ticket_system):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system

    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.success, emoji='<:Discord_Ticket:1410727340182343830>', custom_id='trading_ticket_create_persistent')
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

    @discord.ui.button(label='Selling', style=discord.ButtonStyle.primary, emoji='<:SellingLOGO:1410730163607437344>', custom_id='ticket_selling_option')
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

    @discord.ui.button(label='Buying', style=discord.ButtonStyle.secondary, emoji='🛒', custom_id='ticket_buying')
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
        self.update_buttons()

    def update_buttons(self):
        """Update button visibility based on items list"""
        self.clear_items()
        
        # Always show Add Item button
        add_button = discord.ui.Button(
            label='Add Item', 
            style=discord.ButtonStyle.success, 
            emoji='<:CreateLOGO:1390385790726570130>', 
            custom_id='selling_add_item'
        )
        add_button.callback = self.handle_add_item
        self.add_item(add_button)
        
        # Show Remove Item button only if there are items
        if self.items_list:
            remove_button = discord.ui.Button(
                label='Remove Item', 
                style=discord.ButtonStyle.danger, 
                emoji='<:RemoveLOGO:1410726980114190386>', 
                custom_id='selling_remove_item'
            )
            remove_button.callback = self.handle_remove_item
            self.add_item(remove_button)
            
            # Show Next button if there are items
            next_button = discord.ui.Button(
                label='Next', 
                style=discord.ButtonStyle.primary, 
                emoji='➡️', 
                custom_id='selling_next'
            )
            next_button.callback = self.handle_next_to_payment
            self.add_item(next_button)
        
        # Always show Back button
        back_button = discord.ui.Button(
            label='Back', 
            style=discord.ButtonStyle.secondary, 
            emoji='<:BackLOGO:1410726662328422410>', 
            custom_id='selling_back'
        )
        back_button.callback = self.handle_back_to_options
        self.add_item(back_button)

    async def handle_add_item(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = ItemModal(self, "add")
        await interaction.response.send_modal(modal)

    async def handle_remove_item(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = ItemModal(self, "remove")
        await interaction.response.send_modal(modal)

    async def handle_next_to_payment(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Go to payment method selection
        payment_embed = await self.ticket_system.create_payment_method_embed(interaction.user, self.items_list)
        view = PaymentMethodView(self.ticket_system, self.user_id, self.items_list)
        await interaction.response.edit_message(embed=payment_embed, view=view)

    async def handle_back_to_options(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Go back to ticket options
        options_embed = await self.ticket_system.create_ticket_options_embed(interaction.user)
        view = TicketOptionsView(self.ticket_system, self.user_id)
        await interaction.response.edit_message(embed=options_embed, view=view)

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
            default="Clean",
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
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Invalid Status",
                "Status must be either 'Dupe' or 'Clean'!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Validate quantity
        try:
            quantity = int(self.quantity.value.strip()) if self.quantity.value.strip() else 1
            if quantity <= 0:
                error_embed = await self.parent_view.ticket_system.create_error_embed(
                    "Invalid Quantity",
                    "Quantity must be a positive number!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
        except ValueError:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Invalid Quantity",
                "Quantity must be a valid number!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Use the real stockage system
        stockage_system = StockageSystem()

        # Find the item like in /add_stock
        best_match, duplicates = stockage_system.find_best_match(self.item_name.value.strip(), "None")

        if not best_match:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Item Not Found",
                f"Item '{self.item_name.value}' not found in database!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        if len(duplicates) > 1:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Multiple Items Found",
                f"Multiple items found for '{self.item_name.value}'. Please be more specific with the type!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        item_name, item_data = best_match[0], best_match[1]

        # Check if item is obtainable
        clean_item_name = item_name.split('(')[0].strip()
        obtainable_items = self.parent_view.ticket_system.data.get('obtainable', [])
        if clean_item_name in obtainable_items:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Item Information",
                "This item cannot be added because it is worth less than 2.5M or it is obtainable."
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Get value based on status
        if status == "clean":
            value_key = 'Cash Value'
        else:  # dupe
            value_key = 'Duped Value'

        value_str = item_data.get(value_key, 'N/A')

        if value_str == 'N/A' or not value_str or value_str == "N/A":
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Value Not Available",
                f"No {status} value available for '{item_name}'!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Convert value to number (handle format "48 000 000" with normal and Unicode spaces)
        try:
            if isinstance(value_str, str):
                # Remove all types of spaces (normal, Unicode, etc.) and commas
                import re
                clean_value_str = re.sub(r'[\s,]+', '', value_str)
                value = int(clean_value_str)
            elif isinstance(value_str, (int, float)):
                value = int(value_str)
            else:
                raise ValueError(f"Unsupported value type: {type(value_str)}")
        except (ValueError, TypeError) as e:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Invalid Value",
                f"Invalid {status} value for '{item_name}': {value_str}"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Check if item is worth less than 2.5M
        if value < 2_500_000:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Item Information",
                "This item cannot be added because it is worth less than 2.5M or it is obtainable."
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Clean item name (remove type in parentheses for grouping)
        import re
        clean_name = re.sub(r'\s*\([^)]*\)$', '', item_name).strip()

        # Get item type from the full name
        type_match = re.search(r'\(([^)]*)\)', item_name)
        item_type = type_match.group(1) if type_match else "Unknown"

        item_entry = {
            'name': clean_name,
            'quantity': quantity,
            'status': status.capitalize(),
            'value': value,
            'type': item_type
        }

        if self.action == "add":
            self.parent_view.items_list.append(item_entry)
            action_text = "added to"
        else:  # remove
            # Find and remove the item
            removed = False
            for i, existing_item in enumerate(self.parent_view.items_list):
                if (existing_item['name'] == item_entry['name'] and 
                    existing_item['status'] == item_entry['status'] and
                    existing_item['type'] == item_entry['type']):
                    if existing_item['quantity'] > quantity:
                        existing_item['quantity'] -= quantity
                        removed = True
                        break
                    elif existing_item['quantity'] == quantity:
                        self.parent_view.items_list.pop(i)
                        removed = True
                        break
                    else:
                        error_embed = await self.parent_view.ticket_system.create_error_embed(
                            "Insufficient Quantity",
                            f"Cannot remove {quantity} items. Only {existing_item['quantity']} available!"
                        )
                        await interaction.followup.send(embed=error_embed, ephemeral=True)
                        return

            if not removed:
                error_embed = await self.parent_view.ticket_system.create_error_embed(
                    "Item Information",
                    "This item cannot be removed because it has not been added to your list."
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            action_text = "removed from"

        # Update buttons based on current items
        self.parent_view.update_buttons()

        # Update the embed
        new_embed = await self.parent_view.ticket_system.create_selling_list_embed(
            interaction.user, 
            self.parent_view.items_list
        )

        await interaction.edit_original_response(embed=new_embed, view=self.parent_view)

        success_embed = await self.parent_view.ticket_system.create_error_embed(
            "Success",
            f"✅ {item_entry['name']} x{quantity} ({status.capitalize()}) {action_text} your selling list!"
        )
        success_embed.color = 0x00ff00  # Green color for success
        await interaction.followup.send(embed=success_embed, ephemeral=True)

class PaymentMethodView(discord.ui.View):
    def __init__(self, ticket_system, user_id, items_list):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = items_list

    @discord.ui.button(label='GamePass Method', style=discord.ButtonStyle.success, emoji='🎮', custom_id='payment_gamepass')
    async def gamepass_method(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = UsernameModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Group Donation Method', style=discord.ButtonStyle.primary, emoji='👥', custom_id='payment_group')
    async def group_method(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        await interaction.response.send_message("Group Donation Method will be implemented soon!", ephemeral=True)

    @discord.ui.button(label='Information', style=discord.ButtonStyle.secondary, emoji='ℹ️', custom_id='payment_info')
    async def information(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        info_embed = await self.ticket_system.create_information_embed(interaction.user)
        view = InformationView(self.ticket_system, self.user_id, self.items_list)
        await interaction.response.edit_message(embed=info_embed, view=view)

class InformationView(discord.ui.View):
    def __init__(self, ticket_system, user_id, items_list):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = items_list

    @discord.ui.button(label='How to make GamePass', style=discord.ButtonStyle.success, emoji='🎮', custom_id='info_gamepass_howto')
    async def how_to_gamepass(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = UsernameModal(self, from_info=True)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Back', style=discord.ButtonStyle.secondary, emoji='<:BackLOGO:1410726662328422410>', custom_id='info_back')
    async def back_to_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        payment_embed = await self.ticket_system.create_payment_method_embed(interaction.user, self.items_list)
        view = PaymentMethodView(self.ticket_system, self.user_id, self.items_list)
        await interaction.response.edit_message(embed=payment_embed, view=view)

class UsernameModal(discord.ui.Modal):
    def __init__(self, parent_view, from_info=False):
        super().__init__(title="Roblox Username")
        self.parent_view = parent_view
        self.from_info = from_info

        self.username = discord.ui.TextInput(
            label="Roblox Username",
            placeholder="Enter your Roblox username...",
            required=True,
            max_length=50
        )

        self.add_item(self.username)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        username = self.username.value.strip()
        
        try:
            # Import and use RobloxClient
            from roblox_sync import RobloxClient
            
            # Create client instance
            client = RobloxClient()
            
            # Get user ID by username
            user_id = client.get_user_id_by_username(username)
            
            if not user_id:
                error_embed = await self.parent_view.ticket_system.create_error_embed(
                    "User Not Found",
                    f"Roblox user '{username}' not found!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            # Get user experiences
            experiences = client.get_user_experiences(user_id)
            
            if not experiences:
                error_embed = await self.parent_view.ticket_system.create_error_embed(
                    "No Experiences Found",
                    f"No public experiences found for user '{username}'!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            # Get the first experience ID
            first_experience = experiences[0]
            universe_id = first_experience.get('id')
            
            if not universe_id:
                error_embed = await self.parent_view.ticket_system.create_error_embed(
                    "Invalid Experience",
                    "Could not retrieve experience ID!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            # Create the GamePass creation link
            gamepass_url = f"https://create.roblox.com/dashboard/creations/experiences/{universe_id}/monetization/passes"
            
            # Create result embed
            result_embed = await self.parent_view.ticket_system.create_gamepass_result_embed(
                interaction.user, 
                gamepass_url
            )
            
            await interaction.edit_original_response(embed=result_embed, view=None)
            
        except ImportError:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "System Error",
                "Roblox integration is not available. Please contact an administrator."
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Error",
                f"An error occurred while processing your request: {str(e)}"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

# Import du vrai système de stockage
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from stockage_system import StockageSystem

def setup_trading_ticket_system(bot):
    """Setup function to integrate trading ticket system with the bot"""
    ticket_system = TradingTicketSystem(bot)

    # Add persistent views on bot startup
    bot.add_view(TicketPanelView(ticket_system))

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
