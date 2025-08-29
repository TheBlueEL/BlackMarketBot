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
        self.monitoring_tasks = {}  # Store monitoring tasks
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
        embed.set_footer(text=f"{self.bot.user.name} - Ticket System", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
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
        embed.set_footer(text=f"{self.bot.user.name} - Trading Hub", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_selling_embed(self, user):
        """Create the selling ticket embed"""
        embed = discord.Embed(
            title="<:SellingLOGO:1410730163607437344> Selling Ticket",
            description="Please select which items you wish to sell.",
            color=0x19D600
        )
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
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
            prices_column.append(f"**{total_robux:,} <:RobuxLOGO:1410727587134701639> (Incl. Tax)**")

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

        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
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

        description_lines.append(f"\nFor a total of {total_robux:,} <:RobuxLOGO:1410727587134701639> (Incl. Tax)")
        description_lines.append("\nChoose the method you want to receive your payment.")
        description_lines.append("-# The client will always have to pay first.\n")

        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
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
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_gamepass_result_embed(self, user, experience_url):
        """Create embed showing gamepass creation link"""
        embed = discord.Embed(
            title="<:SellingLOGO:1410730163607437344> Selling Ticket",
            description=f"Your GamePass has been successfully created!\n**GamePass Name:** {gamepass_name}\n**GamePass Price:** {gamepass_price:,} <:RobuxLOGO:1410727587134701639>\n\nPlease now set your GamePass price by clicking this link:\n[**Edit GamePass Price**]({price_link})\n\nWe are now monitoring your GamePass price changes...",
            color=0x00ff00
        )
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_account_confirmation_embed(self, roblox_user_data):
        """Create account confirmation embed"""
        embed = discord.Embed(
            title="Account Confirmation",
            color=0x0099ff
        )

        display_name = roblox_user_data.get('displayName', 'N/A')
        username = roblox_user_data.get('name', 'N/A')

        embed.description = f"**Display Name:** {display_name}\n**Username:** {username}"

        # Set profile picture as thumbnail
        if roblox_user_data.get('avatar_url'):
            embed.set_thumbnail(url=roblox_user_data['avatar_url'])

        embed.set_footer(text=f"{self.bot.user.name} - Account Confirmation", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        return embed

    async def create_group_join_embed(self):
        """Create embed for group joining requirement"""
        embed = discord.Embed(
            title="Transaction Method",
            description="Please click on the link below to join our group:\n[**Group Donation Method**](https://www.roblox.com/communities/34785441/about)",
            color=0x0099ff
        )
        embed.set_footer(text=f"{self.bot.user.name} - Transaction Method", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_waiting_period_embed(self, roblox_username, end_timestamp):
        """Create embed for 2-week waiting period"""
        embed = discord.Embed(
            title="Welcome to our Group!",
            description=f"Welcome @{roblox_username}, you have just joined our group!\nPlease wait 2 weeks to proceed with payment. Once the time has elapsed, you will be automatically pinged in this channel.",
            color=0x00ff88
        )

        faq_text = """
**Why wait 2 weeks?**
➤ To avoid fraud, Roblox has implemented a waiting period for the **Group Payouts** feature. This waiting period has a maximum duration of 2 weeks.

**Are our services reliable?**
➤ Our services are 100% reliable, we collect hundreds and hundreds of vouches visible in channel <#1312591100971843676>

**Why choose us?**
➤ We have **THE highest Robux rate/million** which can go up to **90 robux/million** depending on the quantity of items you sell to us.
"""

        embed.add_field(name="F.A.Q", value=faq_text, inline=False)
        embed.add_field(name="Time remaining:", value=f"<t:{end_timestamp}:R>", inline=False)

        embed.set_footer(text=f"{self.bot.user.name} - Group Donation", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_transaction_ready_embed(self, items_list, total_robux):
        """Create embed when 2-week waiting period is complete"""
        embed = discord.Embed(
            title="Transaction Ready",
            description=f"The 2-week period has elapsed, you can now proceed with the transaction of your items.\n\n**Total Amount:** {total_robux:,} Robux\n**Payment Link:** [**HERE**](https://www.roblox.com/group/configure?id=34785441#!/revenue/payouts)",
            color=0x00ff00
        )
        embed.set_footer(text=f"{self.bot.user.name} - Transaction Ready", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_group_transaction_embed(self, user, items_list, total_robux):
        """Create transaction embed for users already in group"""
        embed = discord.Embed(
            title="Transaction to be Processed",
            description=f"Your request has been received, please wait for our teams to be available.\n\n**Total Amount:** {total_robux:,} Robux\n**Payment Link:** [**HERE**](https://www.roblox.com/group/configure?id=34785441#!/revenue/payouts)",
            color=0xffaa00
        )

        # Create items list for display
        items_text = []
        prices_text = []

        # Group items for display
        grouped_items = {}
        for item in items_list:
            key = f"{item['name']} ({item['type']}) ({item['status']})"
            if key not in grouped_items:
                grouped_items[key] = {'quantity': 0, 'robux_price': 0}

            # Calculate individual robux price for this item
            total_value = sum(i['value'] * i['quantity'] for i in items_list)
            total_millions = total_value / 1_000_000
            robux_rate = self.calculate_robux_rate(total_millions)
            item_robux = int((item['value'] * item['quantity'] / 1_000_000) * robux_rate)

            grouped_items[key]['quantity'] += item['quantity']
            grouped_items[key]['robux_price'] += item_robux

        for item_name, data in grouped_items.items():
            quantity = data['quantity']
            robux_price = data['robux_price']

            if quantity == 1:
                items_text.append(f"• 1x {item_name}")
            else:
                items_text.append(f"• {quantity}x {item_name}")

            prices_text.append(f"{robux_price:,} Robux")

        # Add TOTAL
        items_text.append("**TOTAL**")
        prices_text.append(f"**{total_robux:,} Robux**")

        embed.add_field(
            name="Item",
            value="\n".join(items_text),
            inline=True
        )

        embed.add_field(
            name="Prices",
            value="\n".join(prices_text),
            inline=True
        )

        embed.set_footer(text=f"{self.bot.user.name} - Group Transaction", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        return embed

    async def create_sell_info_embed(self, items_list):
        """Create selling information embed"""
        embed = discord.Embed(
            title="Selling List",
            color=0x0099ff
        )

        # Group items for display
        grouped_items = {}
        total_robux = 0

        for item in items_list:
            key = f"{item['name']} ({item['type']}) ({item['status']})"
            if key not in grouped_items:
                grouped_items[key] = {'quantity': 0, 'robux_price': 0}

            # Calculate individual robux price for this item
            total_value = sum(i['value'] * i['quantity'] for i in items_list)
            total_millions = total_value / 1_000_000
            robux_rate = self.calculate_robux_rate(total_millions)
            item_robux = int((item['value'] * item['quantity'] / 1_000_000) * robux_rate)

            grouped_items[key]['quantity'] += item['quantity']
            grouped_items[key]['robux_price'] += item_robux
            total_robux += item_robux

        # Create items list for display
        items_text = []
        prices_text = []

        for item_name, data in grouped_items.items():
            quantity = data['quantity']
            robux_price = data['robux_price']

            if quantity == 1:
                items_text.append(f"• 1x {item_name}")
            else:
                items_text.append(f"• {quantity}x {item_name}")

            prices_text.append(f"{robux_price:,} Robux")

        # Add TOTAL
        items_text.append("**TOTAL**")
        prices_text.append(f"**{total_robux:,} Robux**")

        embed.add_field(
            name="Item",
            value="\n".join(items_text),
            inline=True
        )

        embed.add_field(
            name="Prices",
            value="\n".join(prices_text),
            inline=True
        )

        embed.set_footer(text=f"{self.bot.user.name} - Selling List", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        return embed

    async def create_gamepass_success_embed(self, user, gamepass_name, gamepass_price, gamepass_id, experience_id):
        """Create embed when GamePass is successfully created"""
        price_link = f"https://create.roblox.com/dashboard/creations/experiences/{experience_id}/passes/{gamepass_id}/sales"

        embed = discord.Embed(
            title="<:SellingLOGO:1410730163607437344> GamePass Created",
            description=f"Your GamePass has been successfully created!\n**GamePass Name:** {gamepass_name}\n**GamePass Price:** {gamepass_price:,} <:RobuxLOGO:1410727587134701639>\n\nPlease now set your GamePass price by clicking this link:\n[**Edit GamePass Price**]({price_link})\n\nWe are now monitoring your GamePass price changes...",
            color=0x00ff00
        )
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_transaction_pending_embed(self, seller_user, seller_username, gamepass_id, items_list, total_robux_pretax):
        """Create transaction pending embed for support team"""
        embed = discord.Embed(
            title="Transaction Pending",
            description=f"Welcome Back <@&1300798850788757564>! {seller_user.mention} wants to sell for {total_robux_pretax:,} Robux (Incl. Tax):",
            color=0xffaa00
        )

        # Group items for display
        grouped_items = {}
        for item in items_list:
            key = f"{item['name']} ({item['type']}) ({item['status']})"
            if key not in grouped_items:
                grouped_items[key] = {'quantity': 0, 'robux_price': 0}

            # Calculate individual robux price for this item
            total_value = sum(i['value'] * i['quantity'] for i in items_list)
            total_millions = total_value / 1_000_000
            robux_rate = self.calculate_robux_rate(total_millions)
            item_robux = int((item['value'] * item['quantity'] / 1_000_000) * robux_rate)

            grouped_items[key]['quantity'] += item['quantity']
            grouped_items[key]['robux_price'] += item_robux

        # Create items list for embed
        items_text = []
        prices_text = []

        for item_name, data in grouped_items.items():
            quantity = data['quantity']
            robux_price = data['robux_price']

            if quantity == 1:
                items_text.append(f"• 1x {item_name}")
            else:
                items_text.append(f"• {quantity}x {item_name}")

            prices_text.append(f"{robux_price:,} Robux")

        embed.add_field(
            name="Items",
            value="\n".join(items_text),
            inline=True
        )

        embed.add_field(
            name="Prices",
            value="\n".join(prices_text),
            inline=True
        )

        embed.add_field(
            name="\u200b",
            value="\u200b",
            inline=True
        )

        # Get user ID for clickable username link
        try:
            from roblox_sync import RobloxClient
            client = RobloxClient()
            user_id = client.get_user_id_by_username(seller_username)
            if user_id:
                username_link = f"[**{seller_username}**](https://www.roblox.com/users/{user_id}/profile)"
            else:
                username_link = seller_username
        except:
            username_link = seller_username

        embed.add_field(
            name="Roblox Username",
            value=username_link,
            inline=False
        )

        embed.add_field(
            name="GamePass Link",
            value=f"[**HERE**](https://www.roblox.com/fr/game-pass/{gamepass_id}/)",
            inline=False
        )

        embed.set_footer(text=f"{self.bot.user.name} - Transaction System", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        return embed

    async def create_price_error_embed(self, user, expected_price, actual_price):
        """Create embed when GamePass price is incorrect"""
        embed = discord.Embed(
            title="<:ErrorLOGO:1387810170155040888> Incorrect Price",
            description=f"Your GamePass price doesn't match the required amount of **{expected_price:,}** <:RobuxLOGO:1410727587134701639>.\nYour current price is **{actual_price:,}** <:RobuxLOGO:1410727587134701639>.\n\nPlease use the previous link again to update your GamePass price to the correct amount.\n-# Please, do not create a new GamePass.",
            color=0xff0000
        )
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_purchase_accepted_embed(self, user):
        """Create embed when purchase is accepted"""
        embed = discord.Embed(
            title="Purchase Accepted",
            description="Our team has accepted your purchase. We will now proceed with the transaction.",
            color=0x00ff00
        )
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    def parse_item_with_hyperchrome(self, item_input):
        """Parse item input to detect hyperchromes and types like /add_stock"""
        try:
            with open('item_request.json', 'r', encoding='utf-8') as f:
                item_data = json.load(f)
        except FileNotFoundError:
            return {'name': item_input, 'type': 'None', 'is_hyperchrome': False}

        # Check for hyperchrome patterns first
        hyper_data = item_data.get('hyper', {})
        for hyper_name, aliases in hyper_data.items():
            for alias in aliases:
                if alias.lower() == item_input.lower():
                    # Found hyperchrome match, get from API with 2023 year
                    try:
                        with open('API_JBChangeLogs.json', 'r', encoding='utf-8') as f:
                            api_data = json.load(f)

                        # Look for hyperchrome with 2023 year
                        hyperchrome_name_2023 = f"{hyper_name} (2023)"
                        if hyperchrome_name_2023 in api_data:
                            return {
                                'name': hyper_name,  # Display name without year
                                'type': 'Hyperchrome',
                                'is_hyperchrome': True,
                                'api_name': hyperchrome_name_2023
                            }

                        # Fallback to original name if 2023 not found
                        if hyper_name in api_data:
                            return {
                                'name': hyper_name,
                                'type': 'Hyperchrome',
                                'is_hyperchrome': True,
                                'api_name': hyper_name
                            }
                    except FileNotFoundError:
                        pass

                    return {
                        'name': hyper_name,
                        'type': 'Hyperchrome',
                        'is_hyperchrome': True
                    }

        # Check for type patterns
        type_data = item_data.get('type', {})
        detected_type = 'None'
        clean_name = item_input

        for type_name, aliases in type_data.items():
            for alias in aliases:
                if alias.lower() in item_input.lower():
                    detected_type = type_name
                    # Remove type from name
                    clean_name = item_input.replace(alias, '').strip()
                    break
            if detected_type != 'None':
                break

        return {
            'name': clean_name,
            'type': detected_type,
            'is_hyperchrome': False
        }

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
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def start_gamepass_monitoring(self, channel, user, username, experience_id, items_list, expected_price):
        """Start monitoring for new GamePass creation"""
        try:
            from roblox_gamepasslink import GamePassLink

            client = GamePassLink()

            # Get initial GamePass list
            initial_gamepasses = client.get_game_passes(experience_id)
            initial_ids = [gp.get('id') for gp in initial_gamepasses if gp.get('id')]

            # Create monitoring task
            task_key = f"{channel.id}_{user.id}"
            if task_key in self.monitoring_tasks:
                self.monitoring_tasks[task_key].cancel()

            # Start monitoring task
            self.monitoring_tasks[task_key] = asyncio.create_task(
                self._monitor_gamepass_creation(
                    channel, user, username, experience_id, items_list, expected_price, initial_ids
                )
            )

        except Exception as e:
            print(f"Error starting GamePass monitoring: {e}")

    async def _monitor_gamepass_creation(self, channel, user, username, experience_id, items_list, expected_price, initial_ids):
        """Monitor for new GamePass creation and price changes"""
        try:
            from roblox_gamepasslink import GamePassLink

            client = GamePassLink()

            while True:
                await asyncio.sleep(5)  # Check every 5 seconds

                try:
                    current_gamepasses = client.get_game_passes(experience_id)
                    current_ids = [gp.get('id') for gp in current_gamepasses if gp.get('id')]

                    # Check for new GamePass
                    new_gamepasses = [gp_id for gp_id in current_ids if gp_id not in initial_ids]

                    if new_gamepasses:
                        # Found new GamePass, get its details
                        new_gamepass_id = new_gamepasses[0]  # Take the first new one

                        # Find the GamePass details
                        new_gamepass = None
                        for gp in current_gamepasses:
                            if gp.get('id') == new_gamepass_id:
                                new_gamepass = gp
                                break

                        if new_gamepass:
                            gamepass_name = new_gamepass.get('name', 'Unknown')
                            gamepass_price = new_gamepass.get('price')

                            # Send creation success embed with price modification link
                            success_embed = await self.create_gamepass_success_embed(
                                user, gamepass_name, gamepass_price or 0, new_gamepass_id, experience_id
                            )
                            await channel.send(embed=success_embed)

                            # Start price monitoring for this GamePass immediately
                            await self._monitor_gamepass_price(
                                channel, user, username, new_gamepass_id, expected_price, items_list
                            )

                            # Stop monitoring for new GamePass creation
                            break

                except Exception as e:
                    print(f"Error in GamePass monitoring: {e}")
                    await asyncio.sleep(10)  # Wait longer on error

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            print(f"Error in GamePass creation monitoring: {e}")

    async def _monitor_gamepass_price(self, channel, user, username, gamepass_id, expected_price, items_list):
        """Monitor GamePass price changes"""
        try:
            from roblox_gamepasslink import GamePassLink
            from roblox_sync import RobloxClient

            gamepass_client = GamePassLink()
            roblox_client = RobloxClient()

            # Get the user ID and experience ID for monitoring
            user_id = roblox_client.get_user_id_by_username(username)
            if not user_id:
                print(f"Could not find user ID for {username}")
                return

            experiences = roblox_client.get_user_experiences(user_id)
            if not experiences:
                print(f"No experiences found for {username}")
                return

            experience_id = experiences[0].get('id')

            last_notified_price = None  # Track the last price we sent an error for

            while True:
                await asyncio.sleep(5)  # Check every 5 seconds

                try:
                    # Get all GamePass from the experience
                    all_gamepasses = gamepass_client.get_game_passes(experience_id)

                    # Find our specific GamePass
                    target_gamepass = None
                    for gp in all_gamepasses:
                        if gp.get('id') == gamepass_id:
                            target_gamepass = gp
                            break

                    if target_gamepass:
                        current_price = target_gamepass.get('price')

                        if current_price is not None and current_price != 0:  # Price was set
                            if current_price == expected_price:
                                # Price is correct! Send transaction pending

                                # Wait 3 seconds first
                                await asyncio.sleep(3)

                                # Calculate total robux for transaction (pre-tax)
                                total_value = sum(item['value'] * item['quantity'] for item in items_list)
                                total_millions = total_value / 1_000_000
                                robux_rate = self.calculate_robux_rate(total_millions)
                                total_robux_pretax = int(total_millions * robux_rate)

                                # Send transaction pending embed (ping outside)
                                pending_embed = await self.create_transaction_pending_embed(
                                    user, username, gamepass_id, items_list, total_robux_pretax
                                )

                                # Create accept button view
                                accept_view = AcceptTransactionView(self, channel, user)

                                await channel.send(
                                    content="<@&1300798850788757564>",
                                    embed=pending_embed,
                                    view=accept_view
                                )

                                # Stop monitoring, transaction is ready
                                break
                            else:
                                # Price is incorrect, only send error if price changed
                                if last_notified_price != current_price:
                                    error_embed = await self.create_price_error_embed(
                                        user, expected_price, current_price
                                    )
                                    await channel.send(
                                        content=user.mention,
                                        embed=error_embed
                                    )
                                    last_notified_price = current_price
                                # Continue monitoring for price changes
                    else:
                        print(f"GamePass {gamepass_id} not found in experience {experience_id}")

                except Exception as e:
                    print(f"Error in GamePass price monitoring: {e}")
                    await asyncio.sleep(10)  # Wait longer on error

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            print(f"Error in GamePass price monitoring: {e}")

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
                emoji='<:NextLOGO:1410972675261857892>',
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
        try:
            await interaction.response.defer()
        except discord.NotFound:
            # Interaction has expired
            try:
                await interaction.followup.send("Interaction expired. Please try again.", ephemeral=True)
            except:
                pass
            return
        except Exception as e:
            print(f"Error deferring modal interaction: {e}")
            return

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

        # Parse item name using item_request.json like /add_stock
        parsed_item = self.parent_view.ticket_system.parse_item_with_hyperchrome(self.item_name.value.strip())

        stockage_system = StockageSystem()

        # Find the item with specific type preference
        item_type = parsed_item.get('type', 'None')
        best_match, duplicates = stockage_system.find_best_match(parsed_item['name'], item_type)

        if not best_match:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Item Not Found",
                f"Item '{self.item_name.value}' not found in database!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Handle duplicates with priority order
        if len(duplicates) > 1:
            # Try to find exact match first, then prefer specific order
            priority_types = ["Vehicle", "Texture", "Body Color", "Rim", "Spoiler", "Weapon Skin", "Tire Sticker", "Tire Style", "Drift", "Furniture", "Horn"]

            # Look for exact name match first
            exact_matches = []
            for item_name_dup, item_data_dup in duplicates:
                clean_name = item_name_dup.split('(')[0].strip().lower()
                input_name = self.item_name.value.strip().lower()
                if clean_name == input_name:
                    exact_matches.append((item_name_dup, item_data_dup))

            if len(exact_matches) == 1:
                best_match = exact_matches[0]
            elif len(exact_matches) > 1:
                # Multiple exact matches, use priority
                for ptype in priority_types:
                    for item_name_dup, item_data_dup in exact_matches:
                        if f"({ptype})" in item_name_dup:
                            best_match = (item_name_dup, item_data_dup)
                            break
                    if best_match:
                        break

                # If no priority type found, take first exact match
                if not best_match:
                    best_match = exact_matches[0]
            else:
                # No exact matches, ask for clarification
                error_embed = await self.parent_view.ticket_system.create_error_embed(
                    "Multiple Items Found",
                    f"Multiple items found for '{self.item_name.value}'. Please be more specific with the type!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

        item_name, item_data = best_match[0], best_match[1]

        # Check if item is obtainable before value check
        clean_item_name = item_name.split('(')[0].strip()

        # Load obtainable items from data file
        try:
            obtainable_items = self.parent_view.ticket_system.data.get('obtainable', [])
        except:
            obtainable_items = []

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

        # Check if item is worth less than 2.5M
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

        # For hyperchromes, remove year from display name
        if item_type == "Hyperchrome":
            # Remove any year (2022, 2023, 2024, etc.) from the clean name
            clean_name = re.sub(r'\b(202[2-9]|20[3-9][0-9])\b', '', clean_name).strip()

        # Get item type from the full name
        type_match = re.search(r'\(([^)]*)\)', item_name)
        final_item_type = type_match.group(1) if type_match else item_type


        item_entry = {
            'name': clean_name,
            'quantity': quantity,
            'status': status.capitalize(),
            'value': value,
            'type': final_item_type
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
            "<:SucessLOGO:1387810153864368218> Item Added",
            f"X{quantity} {item_entry['name']} ({status.capitalize()}) {action_text} your selling list!"
        )
        success_embed.color = 0x00ff00  # Green color for success
        await interaction.followup.send(embed=success_embed, ephemeral=True)

class PaymentMethodView(discord.ui.View):
    def __init__(self, ticket_system, user_id, items_list, disable_back=False):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = items_list
        self.disable_back = disable_back
        self.setup_buttons()

    def setup_buttons(self):
        """Setup buttons with conditional back button state"""
        # GamePass Method button
        gamepass_button = discord.ui.Button(
            label='GamePass Method',
            style=discord.ButtonStyle.success,
            emoji='<:GamePassLOGO:1410971222715531274>',
            custom_id='payment_gamepass'
        )
        gamepass_button.callback = self.gamepass_method
        self.add_item(gamepass_button)

        # Group Donation Method button
        group_button = discord.ui.Button(
            label='Group Donation Method',
            style=discord.ButtonStyle.primary,
            emoji='👥',
            custom_id='payment_group'
        )
        group_button.callback = self.group_method
        self.add_item(group_button)

        # Information button
        info_button = discord.ui.Button(
            label='Information',
            style=discord.ButtonStyle.secondary,
            emoji='<:InformationLOGO:1410970300841066496>',
            custom_id='payment_info',
            row=1
        )
        info_button.callback = self.information
        self.add_item(info_button)

        # Back button (disabled if needed)
        back_button = discord.ui.Button(
            label='Back',
            style=discord.ButtonStyle.secondary,
            emoji='<:BackLOGO:1410726662328422410>',
            custom_id='payment_back',
            disabled=self.disable_back
        )
        back_button.callback = self.back_to_selling
        self.add_item(back_button)

    async def gamepass_method(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = UsernameModal(self, method="gamepass")
        await interaction.response.send_modal(modal)

    async def group_method(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = UsernameModal(self, method="group")
        await interaction.response.send_modal(modal)

    async def information(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        info_embed = await self.ticket_system.create_information_embed(interaction.user)
        view = InformationView(self.ticket_system, self.user_id, self.items_list)
        await interaction.response.edit_message(embed=info_embed, view=view)

    async def back_to_selling(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        if self.disable_back:
            await interaction.response.send_message("This button is currently disabled.", ephemeral=True)
            return

        # Go back to selling form
        selling_embed = await self.ticket_system.create_selling_list_embed(interaction.user, self.items_list)
        view = SellingFormView(self.ticket_system, self.user_id)
        view.items_list = self.items_list  # Restore items list
        view.update_buttons()
        await interaction.response.edit_message(embed=selling_embed, view=view)

class InformationView(discord.ui.View):
    def __init__(self, ticket_system, user_id, items_list):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = items_list

    @discord.ui.button(label='Back', style=discord.ButtonStyle.secondary, emoji='<:BackLOGO:1410726662328422410>', custom_id='info_back')
    async def back_to_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        payment_embed = await self.ticket_system.create_payment_method_embed(interaction.user, self.items_list)
        view = PaymentMethodView(self.ticket_system, self.user_id, self.items_list, disable_back=False)
        await interaction.response.edit_message(embed=payment_embed, view=view)

class UsernameModal(discord.ui.Modal):
    def __init__(self, parent_view, method="gamepass"):
        super().__init__(title="Roblox Username")
        self.parent_view = parent_view
        self.method = method

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
                    f"No username exists with the name '{username}'!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Get user details including avatar
            user_details = client.get_user_details(user_id)
            avatar_url = client.get_user_avatar(user_id)

            roblox_user_data = {
                'id': user_id,
                'name': user_details.get('name', username),
                'displayName': user_details.get('displayName', username),
                'avatar_url': avatar_url
            }

            # Create account confirmation embed
            confirmation_embed = await self.parent_view.ticket_system.create_account_confirmation_embed(roblox_user_data)

            # Create confirmation view
            confirmation_view = AccountConfirmationView(
                self.parent_view.ticket_system,
                self.parent_view.user_id,
                self.parent_view.items_list,
                roblox_user_data,
                self.method
            )

            await interaction.edit_original_response(embed=confirmation_embed, view=confirmation_view)

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

class AccountConfirmationView(discord.ui.View):
    def __init__(self, ticket_system, user_id, items_list, roblox_user_data, method):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = items_list
        self.roblox_user_data = roblox_user_data
        self.method = method

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.success, custom_id='confirm_account')
    async def confirm_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        await interaction.response.defer()

        if self.method == "gamepass":
            await self._handle_gamepass_method(interaction)
        elif self.method == "group":
            await self._handle_group_method(interaction)

    @discord.ui.button(label='Other Account', style=discord.ButtonStyle.secondary, custom_id='other_account')
    async def other_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = UsernameModal(self.ticket_system, self.method)
        await interaction.response.send_modal(modal)

    async def _handle_gamepass_method(self, interaction):
        """Handle GamePass method confirmation"""
        try:
            from roblox_sync import RobloxClient

            client = RobloxClient()
            user_id = self.roblox_user_data['id']

            # Get user experiences
            experiences = client.get_user_experiences(user_id)

            if not experiences:
                error_embed = await self.ticket_system.create_error_embed(
                    "No Experiences Found",
                    f"No public experiences found for this user!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Get the first experience ID
            first_experience = experiences[0]
            universe_id = first_experience.get('id')

            if not universe_id:
                error_embed = await self.ticket_system.create_error_embed(
                    "Invalid Experience",
                    "Could not retrieve experience ID!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Create the GamePass creation link
            gamepass_url = f"https://create.roblox.com/dashboard/creations/experiences/{universe_id}/monetization/passes"

            # Calculate expected price without tax
            total_value = sum(item['value'] * item['quantity'] for item in self.items_list)
            total_millions = total_value / 1_000_000
            robux_rate = self.ticket_system.calculate_robux_rate(total_millions)
            expected_price = int(total_millions * robux_rate)

            # Create result embed
            result_embed = await self.ticket_system.create_gamepass_result_embed(
                interaction.user,
                gamepass_url
            )

            # Update original message with disabled back button
            payment_embed = await self.ticket_system.create_payment_method_embed(interaction.user, self.items_list)
            disabled_view = PaymentMethodView(self.ticket_system, self.user_id, self.items_list, disable_back=True)

            await interaction.edit_original_response(embed=payment_embed, view=disabled_view)
            await interaction.followup.send(embed=result_embed)

            # Start GamePass monitoring
            await self.ticket_system.start_gamepass_monitoring(
                interaction.channel,
                interaction.user,
                self.roblox_user_data['name'],
                universe_id,
                self.items_list,
                expected_price
            )

        except Exception as e:
            error_embed = await self.ticket_system.create_error_embed(
                "Error",
                f"An error occurred: {str(e)}"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    async def _handle_group_method(self, interaction):
        """Handle Group method confirmation"""
        try:
            from roblox_sync import RobloxClient
            from roblox_OnJoinGroup import group_monitor

            client = RobloxClient()
            user_id = self.roblox_user_data['id']
            group_id = 34785441

            # Check if user is in group
            is_in_group = client.is_user_in_group(user_id, group_id)

            # Calculate total robux
            total_value = sum(item['value'] * item['quantity'] for item in self.items_list)
            total_millions = total_value / 1_000_000
            robux_rate = self.ticket_system.calculate_robux_rate(total_millions)
            total_robux = int(total_millions * robux_rate)

            if is_in_group:
                # User already in group - direct transaction
                transaction_embed = await self.ticket_system.create_group_transaction_embed(
                    interaction.user, self.items_list, total_robux
                )

                view = GroupTransactionView(
                    self.ticket_system, interaction.user, self.items_list,
                    total_robux, self.roblox_user_data['name']
                )

                content = f"{interaction.user.mention} <@&1300798850788757564>"
                await interaction.edit_original_response(content=content, embed=transaction_embed, view=view)
            else:
                # User needs to join group
                join_embed = await self.ticket_system.create_group_join_embed()
                await interaction.edit_original_response(embed=join_embed, view=None)

                # Start monitoring for group join using the dedicated module
                if group_monitor:
                    await group_monitor.start_group_monitoring(
                        interaction.channel, interaction.user, user_id, group_id,
                        self.items_list, total_robux, self.roblox_user_data['name'], self.ticket_system
                    )

        except Exception as e:
            error_embed = await self.ticket_system.create_error_embed(
                "Error",
                f"An error occurred: {str(e)}"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

class GroupTransactionView(discord.ui.View):
    def __init__(self, ticket_system, user, items_list, total_robux, roblox_username):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user = user
        self.items_list = items_list
        self.total_robux = total_robux
        self.roblox_username = roblox_username

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success, custom_id='accept_group_transaction')
    async def accept_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has the required role
        required_role_id = 1300798850788757564
        if not any(role.id == required_role_id for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to accept transactions!", ephemeral=True)
            return

        # Allow user to speak in the channel
        overwrites = interaction.channel.overwrites
        if self.user in overwrites:
            overwrites[self.user].send_messages = True
            await interaction.channel.edit(overwrites=overwrites)

        # Send acceptance embed
        accept_embed = await self.ticket_system.create_purchase_accepted_embed(self.user)
        await interaction.response.send_message(embed=accept_embed)

        # Disable the buttons
        self.clear_items()
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label='Refuse', style=discord.ButtonStyle.danger, custom_id='refuse_group_transaction')
    async def refuse_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has the required role
        required_role_id = 1300798850788757564
        if not any(role.id == required_role_id for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to refuse transactions!", ephemeral=True)
            return

        modal = RefuseReasonModal(self.user, interaction.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Sell Information', style=discord.ButtonStyle.secondary, custom_id='sell_info')
    async def sell_information(self, interaction: discord.Interaction, button: discord.ui.Button):
        info_embed = await self.ticket_system.create_sell_info_embed(self.items_list)
        await interaction.response.send_message(embed=info_embed, ephemeral=True)

class RefuseReasonModal(discord.ui.Modal):
    def __init__(self, user, channel):
        super().__init__(title="Refuse Reason")
        self.user = user
        self.channel = channel

        self.reason = discord.ui.TextInput(
            label="Reason for refusal",
            placeholder="Enter the reason for refusing this transaction...",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )

        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Create refusal embed for DM
        refuse_embed = discord.Embed(
            title="Sell Request Refused",
            description=f"Your selling request has been refused by our staff for these reasons:\n{self.reason.value}",
            color=0xff0000
        )

        try:
            # Send DM to user
            await self.user.send(embed=refuse_embed)
            await interaction.followup.send("Refusal reason sent to user via DM.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("Could not send DM to user, but transaction was refused.", ephemeral=True)

        # Delete the channel after a short delay
        await asyncio.sleep(5)
        await self.channel.delete(reason="Transaction refused by staff")

class AcceptTransactionView(discord.ui.View):
    def __init__(self, ticket_system, channel, user):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.channel = channel
        self.user = user

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success, emoji='<:ConfirmLOGO:1410970202191171797>', custom_id='accept_transaction')
    async def accept_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has the required role
        required_role_id = 1300798850788757564
        if not any(role.id == required_role_id for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to accept transactions!", ephemeral=True)
            return

        # Allow user to speak in the channel
        overwrites = self.channel.overwrites
        if self.user in overwrites:
            overwrites[self.user].send_messages = True
            await self.channel.edit(overwrites=overwrites)

        # Send acceptance embed
        accept_embed = await self.ticket_system.create_purchase_accepted_embed(self.user)
        await interaction.response.send_message(embed=accept_embed)

        # Disable the buttons
        self.clear_items()
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label='Refuse', style=discord.ButtonStyle.danger, emoji='<:RefuseLOGO:1410970076102901790>', custom_id='refuse_gamepass_transaction')
    async def refuse_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has the required role
        required_role_id = 1300798850788757564
        if not any(role.id == required_role_id for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to refuse transactions!", ephemeral=True)
            return

        modal = RefuseReasonModal(self.user, self.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Sell Information', style=discord.ButtonStyle.secondary, emoji='<:InformationLOGO:1410970300841066496>', custom_id='gamepass_sell_info')
    async def sell_information(self, interaction: discord.Interaction, button: discord.ui.Button):
        # This would require access to the items list, we'll implement this later
        await interaction.response.send_message("Sell information feature will be implemented.", ephemeral=True)

# Import du vrai système de stockage
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from stockage_system import StockageSystem

def setup_trading_ticket_system(bot):
    """Setup function to integrate trading ticket system with the bot"""
    ticket_system = TradingTicketSystem(bot)

    # Setup group monitor
    from roblox_OnJoinGroup import setup_group_monitor
    setup_group_monitor(bot)

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
    return ticket_system