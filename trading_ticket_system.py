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
        self.channel_types = {
            'default': '𝐓𝐢𝐜𝐤𝐞𝐭',
            'selling': '𝐒𝐞𝐥𝐥',
            'buying': '𝐁𝐮𝐲'
        }
        self.special_dict = {
            # Minuscules
            "a": "𝐚", "b": "𝐛", "c": "𝐜", "d": "𝐝", "e": "𝐞",
            "f": "𝐟", "g": "𝐠", "h": "𝐡", "i": "𝐢", "j": "𝐣",
            "k": "𝐤", "l": "𝐥", "m": "𝐦", "n": "𝐧", "o": "𝐨",
            "p": "𝐩", "q": "𝐪", "r": "𝐫", "s": "𝐬", "t": "𝐭",
            "u": "𝐮", "v": "𝐯", "w": "𝐰", "x": "𝐱", "y": "𝐲", "z": "𝐳",

            # Majuscules
            "A": "𝐀", "B": "𝐁", "C": "𝐂", "D": "𝐃", "E": "𝐄",
            "F": "𝐅", "G": "𝐆", "H": "𝐇", "I": "𝐈", "J": "𝐉",
            "K": "𝐊", "L": "𝐋", "M": "𝐌", "N": "𝐍", "O": "𝐎",
            "P": "𝐏", "Q": "𝐐", "R": "𝐑", "S": "𝐒", "T": "𝐓",
            "U": "𝐔", "V": "𝐕", "W": "𝐖", "X": "𝐗", "Y": "𝐘", "Z": "𝐙",

            # Chiffres
            "0": "𝟎", "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒",
            "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗",

            # Caractères spéciaux
            ".": ".",
            "_": "_"
        }
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
                "active_tickets": {},
                "ticket_states": {}  # Store ticket states for persistence
            }
            self.save_data()

        # Ensure ticket_states exists for existing data files
        if "ticket_states" not in self.data:
            self.data["ticket_states"] = {}
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
            color=0x19D600
        )

        if not items_list:
            embed.description = "Please select which items you wish to sell."
        else:
            # Group items by name and type, keeping status for calculations
            grouped_items = {}
            total_value = 0

            for item in items_list:
                # Format item name - don't show (HyperChrome) for hyperchromes, always show status
                if item['type'] == 'HyperChrome':
                    key = f"{item['name']} ({item['status']})"
                else:
                    key = f"{item['name']} ({item['type']}) ({item['status']})"

                if key not in grouped_items:
                    grouped_items[key] = {'quantity': 0, 'total_value': 0}

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
            color=0x00D61C
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
            # Format item name - don't show (HyperChrome) for hyperchromes, always show status
            if item['type'] == 'HyperChrome':
                key = f"{item['name']} ({item['status']})"
            else:
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
                description_lines.append(f"• {quantity}x {item_name} {robux_price:,} <:RobuxLOGO:1410727587134701639> ({per_item_price:,} <:RobuxLOGO:1410727587134701639> x{quantity})")

        description_lines.append(f"\nFor a total of {total_robux:,} <:RobuxLOGO:1410727587134701639> (Incl. Tax)")
        description_lines.append("\nChoose the method you want to receive your payment.")
        description_lines.append("-# <:InformationLOGO:1410970300841066496> The client will always have to pay first.\n")

        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_information_embed(self, user):
        """Create the information embed explaining payment methods"""
        embed = discord.Embed(
            title="<:InformationLOGO:1410970300841066496> Selling Information",
            color=0xFFFFFF
        )

        description_lines = [
            "**<:GamePassLOGO:1410971222715531274> GamePass Method**",
            'The "**GamePass Method**" consists of **creating a Gamepass** on an experience where you can set the price of the amount we will have to pay. This payment is made instantly depending on the availability of our teams.',
            "",
            "**<:GroupLOGO:1411125220873474179> roup Donation Method**",
            'The "**Group Donation Method**" consists of joining our Roblox group in order to receive, after a delay of 2 weeks, implemented by Roblox, your transaction.'
        ]

        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_gamepass_result_embed(self, user, gamepass_url):
        """Create embed showing gamepass creation link"""
        embed = discord.Embed(
            title="<:SellingLOGO:1410730163607437344> GamePass Creation",
            description=f"Please create a GamePass using the link below:\n\n[**Create GamePass**]({gamepass_url})\n\nOnce created, we will automatically detect it and guide you through setting the correct price.\n\nWe are now monitoring for new GamePass creation...",
            color=0x00ff88
        )
        embed.set_footer(text=f"{self.bot.user.name} - Selling Ticket", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_account_confirmation_embed(self, roblox_user_data):
        """Create account confirmation embed"""
        embed = discord.Embed(
            title="<:ParticipantsLOGO:1388214072188862574> Account Confirmation",
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
            title="<:GroupLOGO:1411125220873474179> Group Donation Method",
            description="Please click on the link below to join our group:\n[**Group Donation Method**](https://www.roblox.com/communities/34785441/about)",
            color=0x0099ff
        )
        embed.set_footer(text=f"{self.bot.user.name} - Transaction Method", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_waiting_period_embed(self, roblox_username, end_timestamp):
        """Create embed for 2-week waiting period with persistent countdown"""
        import time
        
        current_time = int(time.time())
        time_remaining = end_timestamp - current_time
        
        if time_remaining <= 0:
            # Time has already expired
            embed = discord.Embed(
                title="<:GroupLOGO:1411125220873474179> Transaction Ready!",
                description=f"Welcome @{roblox_username}, the 2-week waiting period has completed! You can now proceed with your transaction.",
                color=0x00ff00
            )
        else:
            # Calculate days, hours, minutes, seconds
            days = time_remaining // 86400
            hours = (time_remaining % 86400) // 3600
            minutes = (time_remaining % 3600) // 60
            seconds = time_remaining % 60
            
            time_text = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
            
            embed = discord.Embed(
                title="<:GroupLOGO:1411125220873474179> Welcome to our Group!",
                description=f"Welcome @{roblox_username}, you have just joined our group! We will now proceed with the transfer of vehicles.\n\n**Time remaining:** {time_text}\n\nPlease note that when you join our group, payment can be made within 2 weeks.",
                color=0x00ff88
            )

        faq_text = """
**Why wait 2 weeks?**
➤ To avoid fraud, Roblox has implemented a waiting period for the **Group Payouts** feature. This waiting period has a maximum duration of 2 weeks.

**Are our services reliable?**
➤ Our services are 100% reliable, we collect hundreds and hundreds of vouches visible in channel <#1312591100971843676>

**Why choose us?**
➤ We have **THE highest Robux rate/million** which can go up to **90 <:RobuxLOGO:1410727587134701639>/million** depending on the quantity of items you sell to us.
"""

        embed.add_field(name="F.A.Q", value=faq_text, inline=False)

        embed.set_footer(text=f"{self.bot.user.name} - Group Donation", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_transaction_ready_embed(self, items_list, total_robux):
        """Create embed when 2-week waiting period is complete"""
        embed = discord.Embed(
            title="Transaction Ready",
            description=f"The 2-week period has elapsed, you can now proceed with the transaction of your items.\n\n**Total Amount:** {total_robux:,} <:RobuxLOGO:1410727587134701639>\n**Payment Link:** [**HERE**](https://www.roblox.com/communities/configure?id=34785441/revenue/payouts)",
            color=0x00ff00
        )
        embed.set_footer(text=f"{self.bot.user.name} - Transaction Ready", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_cancel_confirmation_embed(self):
        """Create embed for cancel confirmation"""
        embed = discord.Embed(
            title="<:ErrorLOGO:1387810170155040888> Cancel Transaction",
            description="Are you sure you want to stop selling? Canceling this ticket will be completely deleted and there will be no going back.",
            color=0xff0000
        )
        embed.set_footer(text=f"{self.bot.user.name} - Cancel Confirmation", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    async def create_group_transaction_embed(self, user, items_list, total_robux, roblox_username=None, user_id=None):
        """Create transaction embed for users already in group"""
        description_parts = [
            "Your request has been received, please wait for our teams to be available."
        ]

        if roblox_username and user_id:
            description_parts.append(f"\n**Roblox Username:** [**{roblox_username}**](https://www.roblox.com/users/{user_id}/profile)")

        description_parts.append(f"**Total Amount:** {total_robux:,} <:RobuxLOGO:1410727587134701639>")
        description_parts.append("**Payment Link:** [**HERE**](https://www.roblox.com/communities/configure?id=34785441/revenue/payouts)")

        embed = discord.Embed(
            title="<:SucessLOGO:1387810153864368218> Request Sucess",
            description="\n".join(description_parts),
            color=0x37C700
        )

        # Create items list for display
        items_text = []
        prices_text = []

        # Group items for display
        grouped_items = {}
        for item in items_list:
            # Format item name - don't show (HyperChrome) for hyperchromes, always show status
            if item['type'] == 'HyperChrome':
                key = f"{item['name']} ({item['status']})"
            else:
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

            # Format item name with quantity prefix
            if quantity == 1:
                full_item_text = f"• 1x {item_name}"
            else:
                full_item_text = f"• {quantity}x {item_name}"

            # Limit to maximum 40 characters per line, breaking at 32 characters
            if len(full_item_text) > 32:
                # Find a good breaking point
                break_point = 32
                for i in range(32, min(40, len(full_item_text))):
                    if full_item_text[i] in [' ', '(', ')', '-']:
                        break_point = i
                        break

                line1 = full_item_text[:break_point]
                line2 = full_item_text[break_point:break_point+40].strip()
                formatted_item = f"{line1}\n{line2}" if line2 else line1
            else:
                formatted_item = full_item_text

            items_text.append(formatted_item)
            prices_text.append(f"{robux_price:,} <:RobuxLOGO:1410727587134701639>")

        # Add TOTAL
        items_text.append("**TOTAL**")
        prices_text.append(f"**{total_robux:,} <:RobuxLOGO:1410727587134701639>**")

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
            # Format item name - don't show (HyperChrome) for hyperchromes, always show status
            if item['type'] == 'HyperChrome':
                key = f"{item['name']} ({item['status']})"
            else:
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

            # Format item name with quantity prefix
            if quantity == 1:
                full_item_text = f"• 1x {item_name}"
            else:
                full_item_text = f"• {quantity}x {item_name}"

            # Limit to maximum 40 characters per line, breaking at 32 characters
            if len(full_item_text) > 32:
                # Find a good breaking point
                break_point = 32
                for i in range(32, min(40, len(full_item_text))):
                    if full_item_text[i] in [' ', '(', ')', '-']:
                        break_point = i
                        break

                line1 = full_item_text[:break_point]
                line2 = full_item_text[break_point:break_point+40].strip()
                formatted_item = f"{line1}\n{line2}" if line2 else line1
            else:
                formatted_item = full_item_text

            items_text.append(formatted_item)
            prices_text.append(f"{robux_price:,} <:RobuxLOGO:1410727587134701639>")

        # Add TOTAL
        items_text.append("**TOTAL**")
        prices_text.append(f"**{total_robux:,} <:RobuxLOGO:1410727587134701639>**")

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
            description=f"Your GamePass has been successfully created!\n**GamePass Name:** {gamepass_name}\n**Current GamePass Price:** {gamepass_price:,} <:RobuxLOGO:1410727587134701639>\n\nPlease now set your GamePass price by clicking this link:\n[**Edit GamePass Price**]({price_link})\n\nWe are now monitoring your GamePass price changes...",
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
            description=f"Welcome Back <@&1300798850788757564>! {seller_user.mention} wants to sell for {total_robux_pretax:,} <:RobuxLOGO:1410727587134701639> (Incl. Tax):",
            color=0xffaa00
        )

        # Group items for display
        grouped_items = {}
        for item in items_list:
            # Format item name - don't show (HyperChrome) for hyperchromes, always show status
            if item['type'] == 'HyperChrome':
                key = f"{item['name']} ({item['status']})"
            else:
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

            # Format item name with quantity prefix
            if quantity == 1:
                full_item_text = f"• 1x {item_name}"
            else:
                full_item_text = f"• {quantity}x {item_name}"

            # Limit to maximum 40 characters per line, breaking at 32 characters
            if len(full_item_text) > 32:
                # Find a good breaking point
                break_point = 32
                for i in range(32, min(40, len(full_item_text))):
                    if full_item_text[i] in [' ', '(', ')', '-']:
                        break_point = i
                        break

                line1 = full_item_text[:break_point]
                line2 = full_item_text[break_point:break_point+40].strip()
                formatted_item = f"{line1}\n{line2}" if line2 else line1
            else:
                formatted_item = full_item_text

            items_text.append(formatted_item)
            prices_text.append(f"{robux_price:,} <:RobuxLOGO:1410727587134701639>")

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

    async def create_selling_accepted_embed(self, user, channel_id):
        """Create embed when selling is accepted"""
        embed = discord.Embed(
            title="Selling Accepted",
            description="Our team has accepted your selling request. We will now proceed with the transaction.",
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
            with open('API_JBChangeLogs.json', 'r', encoding='utf-8') as f:
                api_data = json.load(f)
        except FileNotFoundError:
            return {'name': item_input, 'type': 'None', 'is_hyperchrome': False}

        # Check for hyperchrome patterns first
        hyper_data = item_data.get('hyper', {})

        # First pass: look for exact matches in aliases (priorité absolue)
        input_stripped = item_input.strip()
        for hyper_name, aliases in hyper_data.items():
            for alias in aliases:
                if alias.lower().strip() == input_stripped.lower():
                    print(f"DEBUG: Found exact alias match '{alias}' for input '{input_stripped}' -> {hyper_name}")
                    return self._get_hyperchrome_from_api(hyper_name, api_data)

        # Second pass: try to match partial patterns like "Purple 5" → "HyperPurple Level 5"
        # Also handle "Hypershift Level 5" → "HyperShift Level 5"
        input_lower = item_input.lower().strip()

        # Extract color and level from input
        import re

        # Pattern for "Color Level" or "Color L" or just "Color Number"
        color_level_patterns = [
            r'^(blue|red|yellow|orange|pink|purple|diamond|green)\s+(level\s*)?(\d+)$',
            r'^(blue|red|yellow|orange|pink|purple|diamond|green)\s+l(\d+)$',
            r'^(blue|red|yellow|orange|pink|purple|diamond|green)\s+(\d+)$',
            # Add patterns for hyperchromes with "hyper" prefix
            r'^hyper(shift|blue|red|yellow|orange|pink|purple|diamond|green)\s+(level\s*)?(\d+)$',
            r'^hyper(shift|blue|red|yellow|orange|pink|purple|diamond|green)\s+l(\d+)$',
            r'^hyper(shift|blue|red|yellow|orange|pink|purple|diamond|green)\s+(\d+)$'
        ]

        for pattern in color_level_patterns:
            match = re.match(pattern, input_lower)
            if match:
                color = match.group(1).capitalize()
                level = match.group(-1)  # Last group is always the number

                # Try to find exact matching hyperchrome
                target_name = f"Hyper{color} Level {level}"
                print(f"DEBUG: Pattern match found, looking for '{target_name}'")
                if target_name in hyper_data:
                    return self._get_hyperchrome_from_api(target_name, api_data)

        # Third pass: check if input might be a hyperchrome name directly
        for hyper_name in hyper_data.keys():
            # Check if input matches the hyperchrome name pattern
            clean_hyper = hyper_name.lower().replace("hyper", "").replace("level", "").replace("l", "").strip()
            clean_input = input_lower.replace("hyper", "").replace("level", "").replace("l", "").strip()

            if clean_input in clean_hyper or clean_hyper in clean_input:
                return self._get_hyperchrome_from_api(hyper_name, api_data)

        # Check for type patterns if not hyperchrome
        type_data = item_data.get('type', {})
        detected_type = 'None'
        clean_name = item_input

        for type_name, aliases in type_data.items():
            for alias in aliases:
                if alias.lower() in item_input.lower():
                    detected_type = type_name
                    clean_name = item_input.replace(alias, '').strip()
                    break
            if detected_type != 'None':
                break

        return {
            'name': clean_name,
            'type': detected_type,
            'is_hyperchrome': False
        }

    def _get_hyperchrome_from_api(self, hyper_name, api_data):
        """Get hyperchrome from API, prioritizing 2023 version"""
        print(f"DEBUG: Looking for hyperchrome '{hyper_name}' in API")

        # Look for hyperchrome with 2023 year first
        hyperchrome_name_2023 = f"{hyper_name} 2023 (HyperChrome)"
        print(f"DEBUG: Trying to find '{hyperchrome_name_2023}'")
        if hyperchrome_name_2023 in api_data:
            print(f"DEBUG: Found 2023 version: {hyperchrome_name_2023}")
            return {
                'name': hyper_name,  # Display name without (HyperChrome)
                'type': 'HyperChrome',
                'is_hyperchrome': True,
                'api_name': hyperchrome_name_2023
            }

        # Try without year but with HyperChrome tag
        hyperchrome_name_normal = f"{hyper_name} (HyperChrome)"
        print(f"DEBUG: Trying to find '{hyperchrome_name_normal}'")
        if hyperchrome_name_normal in api_data:
            print(f"DEBUG: Found normal version: {hyperchrome_name_normal}")
            return {
                'name': hyper_name,
                'type': 'HyperChrome',
                'is_hyperchrome': True,
                'api_name': hyperchrome_name_normal
            }

        # Check all API keys that contain the hyper name
        print(f"DEBUG: Searching all API keys containing '{hyper_name}'")
        for api_key in api_data.keys():
            if hyper_name in api_key and "(HyperChrome)" in api_key:
                print(f"DEBUG: Found matching key: {api_key}")
                return {
                    'name': hyper_name,
                    'type': 'HyperChrome',
                    'is_hyperchrome': True,
                    'api_name': api_key
                }

        # Fallback to original name if found in API
        if hyper_name in api_data:
            print(f"DEBUG: Found exact match: {hyper_name}")
            return {
                'name': hyper_name,
                'type': 'HyperChrome',
                'is_hyperchrome': True,
                'api_name': hyper_name
            }

        print(f"DEBUG: No match found for '{hyper_name}'")
        # Return even if not found in API
        return {
            'name': hyper_name,
            'type': 'HyperChrome',
            'is_hyperchrome': True
        }

    def calculate_robux_rate(self, total_millions):
        """Calculate Robux rate based on total value in millions"""
        if total_millions < 150:
            return 80  # 80 robux per million
        elif total_millions < 300:
            return 85  # 85 robux per million
        else:
            return 90  # 90 robux per million

    def convert_to_special_font(self, text):
        """Convert text to special Unicode font"""
        converted = ""
        for char in text:
            converted += self.special_dict.get(char, char)
        return converted

    async def update_channel_type(self, channel, user, channel_type):
        """Update channel name based on ticket type"""
        username_special = self.convert_to_special_font(user.name.lower())
        new_channel_name = f"『🎟️』{self.channel_types[channel_type]}・{username_special}"
        try:
            await channel.edit(name=new_channel_name)
            # Save channel type to persistent state
            self.save_ticket_state(channel.id, user.id, {'channel_type': channel_type})
        except Exception as e:
            print(f"Error updating channel name: {e}")

    def save_ticket_state(self, channel_id, user_id, state_data):
        """Save ticket state for persistence"""
        channel_key = str(channel_id)
        if channel_key not in self.data['ticket_states']:
            self.data['ticket_states'][channel_key] = {
                'user_id': user_id,
                'channel_type': 'default',
                'current_step': 'options',
                'items_list': [],
                'payment_method': None,
                'roblox_user_data': None,
                'monitoring_data': None
            }

        # Update with new state data
        self.data['ticket_states'][channel_key].update(state_data)
        self.save_data()

    def get_ticket_state(self, channel_id):
        """Get ticket state"""
        channel_key = str(channel_id)
        return self.data['ticket_states'].get(channel_key, None)

    def remove_ticket_state(self, channel_id):
        """Remove ticket state when ticket is closed"""
        channel_key = str(channel_id)
        if channel_key in self.data['ticket_states']:
            del self.data['ticket_states'][channel_key]
            self.save_data()

    async def restore_ticket_view(self, channel, user_id):
        """Restore the appropriate view based on saved state"""
        state = self.get_ticket_state(channel.id)
        if not state:
            return None

        user = self.bot.get_user(user_id)
        if not user:
            return None

        current_step = state.get('current_step', 'options')
        items_list = state.get('items_list', [])

        if current_step == 'options':
            embed = await self.create_ticket_options_embed(user)
            view = TicketOptionsView(self, user_id)
            return embed, view

        elif current_step == 'selling':
            embed = await self.create_selling_list_embed(user, items_list)
            view = SellingFormView(self, user_id, items_list)
            view.update_buttons()
            return embed, view

        elif current_step == 'payment_method':
            embed = await self.create_payment_method_embed(user, items_list)
            view = PaymentMethodView(self, user_id, items_list)
            return embed, view

        elif current_step == 'information':
            embed = await self.create_information_embed(user)
            view = InformationView(self, user_id, items_list)
            return embed, view

        elif current_step == 'account_confirmation':
            roblox_user_data = state.get('roblox_user_data')
            payment_method = state.get('payment_method')
            if roblox_user_data and payment_method:
                embed = await self.create_account_confirmation_embed(roblox_user_data)
                view = AccountConfirmationView(self, user_id, items_list, roblox_user_data, payment_method)
                return embed, view

        elif current_step == 'gamepass_monitoring':
            monitoring_data = state.get('monitoring_data')
            if monitoring_data:
                # Restore gamepass monitoring
                await self.start_gamepass_monitoring(
                    channel, user, monitoring_data['username'],
                    monitoring_data['experience_id'], items_list,
                    monitoring_data['expected_price']
                )

        elif current_step == 'group_monitoring':
            monitoring_data = state.get('monitoring_data')
            if monitoring_data:
                # Restore group monitoring
                from roblox_OnJoinGroup import group_monitor
                if group_monitor:
                    await group_monitor.start_group_monitoring(
                        channel, user, monitoring_data['user_id'],
                        monitoring_data['group_id'], items_list,
                        monitoring_data['total_robux'], monitoring_data['roblox_username'], self
                    )

        elif current_step == 'waiting_period':
            # Restore waiting period countdown
            end_timestamp = state.get('end_timestamp')
            total_robux = state.get('total_robux')
            roblox_username = state.get('roblox_username')
            user_id_roblox = state.get('user_id')
            
            if end_timestamp and total_robux and roblox_username:
                import time
                current_time = int(time.time())
                
                if current_time >= end_timestamp:
                    # Time has expired, show transaction ready
                    embed = await self.create_group_transaction_embed(
                        user, items_list, total_robux, roblox_username, user_id_roblox
                    )
                    view = GroupTransactionView(self, user, items_list, total_robux, roblox_username)
                    return embed, view
                else:
                    # Time still remaining, continue countdown
                    embed = await self.create_waiting_period_embed(roblox_username, end_timestamp)
                    view = WaitingPeriodView(self, user, items_list, total_robux, roblox_username, user_id_roblox, end_timestamp)
                    return embed, view

        return None

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

        # Create channel with special font
        username_special = self.ticket_system.convert_to_special_font(interaction.user.name.lower())
        channel_name = f"『🎟️』{self.ticket_system.channel_types['default']}・{username_special}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            reason=f"Trading ticket created by {interaction.user}"
        )

        # Save ticket data
        self.ticket_system.data['active_tickets'][user_id] = ticket_channel.id
        self.ticket_system.save_data()

        # Save initial ticket state
        self.ticket_system.save_ticket_state(ticket_channel.id, interaction.user.id, {
            'channel_type': 'default',
            'current_step': 'options'
        })

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

    @discord.ui.button(label='Selling', style=discord.ButtonStyle.primary, emoji='<:SellingLOGO:1410730163607437344>', custom_id=f'ticket_selling_option')
    async def selling_option(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        user_id = state.get('user_id')

        # Update channel name to selling type
        await self.ticket_system.update_channel_type(interaction.channel, interaction.user, 'selling')

        # Save selling state
        self.ticket_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'selling',
            'items_list': []
        })

        # Create selling embed
        selling_embed = await self.ticket_system.create_selling_embed(interaction.user)

        # Create selling form view
        selling_view = SellingFormView(self.ticket_system, user_id, [])

        # Update the message with selling embed and form buttons
        await interaction.response.edit_message(embed=selling_embed, view=selling_view)

        # Notify support team
        support_roles = self.ticket_system.get_support_roles(interaction.guild)
        if support_roles:
            role_mentions = " ".join([role.mention for role in support_roles])
            await interaction.followup.send(f"🔔 {role_mentions} New selling ticket created by {interaction.user.mention}!")

    @discord.ui.button(label='Buying', style=discord.ButtonStyle.secondary, emoji='🛒', custom_id=f'ticket_buying')
    async def buying_option(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        user_id = state.get('user_id')

        # Update channel name to buying type
        await self.ticket_system.update_channel_type(interaction.channel, interaction.user, 'buying')

        # Save buying state
        self.ticket_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'buying'
        })

        await interaction.response.send_message("Buying option will be implemented soon! Please choose Selling for now.", ephemeral=True)

class SellingFormView(discord.ui.View):
    def __init__(self, ticket_system, user_id, items_list=None):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = items_list or []
        self.setup_buttons()

    def setup_buttons(self):
        """Setup buttons with persistent custom_ids"""
        self.clear_items()

        # Always show Add Item button
        add_button = discord.ui.Button(
            label='Add Item',
            style=discord.ButtonStyle.success,
            emoji='<:CreateLOGO:1390385790726570130>',
            custom_id='selling_add_item_persistent'
        )
        add_button.callback = self.handle_add_item
        self.add_item(add_button)

        # Show Remove Item button only if there are items
        if self.items_list:
            remove_button = discord.ui.Button(
                label='Remove Item',
                style=discord.ButtonStyle.danger,
                emoji='<:RemoveLOGO:1410726980114190386>',
                custom_id='selling_remove_item_persistent'
            )
            remove_button.callback = self.handle_remove_item
            self.add_item(remove_button)

            # Show Next button if there are items
            next_button = discord.ui.Button(
                label='Next',
                style=discord.ButtonStyle.primary,
                emoji='<:NextLOGO:1410972675261857892>',
                custom_id='selling_next_persistent'
            )
            next_button.callback = self.handle_next_to_payment
            self.add_item(next_button)

        # Always show Back button
        back_button = discord.ui.Button(
            label='Back',
            style=discord.ButtonStyle.secondary,
            emoji='<:BackLOGO:1410726662328422410>',
            custom_id='selling_back_persistent'
        )
        back_button.callback = self.handle_back_to_options
        self.add_item(back_button)

    def update_buttons(self):
        """Update button visibility based on items list"""
        self.setup_buttons()

    async def handle_add_item(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = ItemModal(self, "add")
        await interaction.response.send_modal(modal)

    async def handle_remove_item(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = ItemModal(self, "remove")
        await interaction.response.send_modal(modal)

    async def handle_next_to_payment(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        user_id = state.get('user_id')
        items_list = state.get('items_list', [])

        # Save payment method state
        self.ticket_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'payment_method',
            'items_list': items_list
        })

        # Go to payment method selection
        payment_embed = await self.ticket_system.create_payment_method_embed(interaction.user, items_list)
        view = PaymentMethodView(self.ticket_system, user_id, items_list)
        await interaction.response.edit_message(embed=payment_embed, view=view)

    async def handle_back_to_options(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        user_id = state.get('user_id')

        # Keep current channel type, don't reset to default
        # Save options state without changing channel type
        self.ticket_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'options',
            'items_list': []
        })

        # Go back to ticket options
        options_embed = await self.ticket_system.create_ticket_options_embed(interaction.user)
        view = TicketOptionsView(self.ticket_system, user_id)
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
                "<:ErrorLOGO:1387810170155040888> Item Not Found",
                f"The **{self.item_name.value}** not found in our database."
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Handle duplicates with priority order
        if len(duplicates) > 1:
            # Use priority order from item_request.json
            try:
                with open('item_request.json', 'r', encoding='utf-8') as f:
                    item_request_data = json.load(f)
                priority_order = item_request_data.get('priority_order', {
                    "HyperChrome": 0, "Vehicle": 1, "Rim": 2, "Spoiler": 3, "Body Color": 4, "Texture": 5,
                    "Tire Sticker": 6, "Tire Style": 7, "Drift": 8, "Furniture": 9, "Horn": 10, "Weapon Skin": 11
                })
            except:
                priority_order = {
                    "HyperChrome": 0, "Vehicle": 1, "Rim": 2, "Spoiler": 3, "Body Color": 4, "Texture": 5,
                    "Tire Sticker": 6, "Tire Style": 7, "Drift": 8, "Furniture": 9, "Horn": 10, "Weapon Skin": 11
                }

            # Look for exact name match first
            exact_matches = []
            for item_name_dup, item_data_dup in duplicates:
                clean_name = item_name_dup.split('(')[0].strip().lower()
                input_name = self.item_name.value.strip().lower()
                if clean_name == input_name:
                    exact_matches.append((item_name_dup, item_data_dup))

            def get_priority_score(item_tuple):
                item_name_dup, item_data_dup = item_tuple
                # Extract type from item name
                if "(HyperChrome)" in item_name_dup or "hyperchrome" in item_name_dup.lower():
                    item_type_detected = "HyperChrome"
                else:
                    import re
                    match = re.search(r'\(([^)]+)\)$', item_name_dup)
                    if match:
                        item_type_detected = match.group(1)
                    else:
                        item_type_detected = "Unknown"

                # Return priority score (lower = higher priority)
                return priority_order.get(item_type_detected, 999)

            if len(exact_matches) == 1:
                best_match = exact_matches[0]
            elif len(exact_matches) > 1:
                # Multiple exact matches, use priority order
                sorted_matches = sorted(exact_matches, key=get_priority_score)
                best_match = sorted_matches[0]
            else:
                # No exact matches, use priority order on all duplicates
                sorted_duplicates = sorted(duplicates, key=get_priority_score)
                best_match = sorted_duplicates[0]

        item_name, item_data = best_match[0], best_match[1]

        # Check if item is obtainable before value check
        clean_item_name = item_name.split('(')[0].strip()

        # Vérifier la valeur minimale (2.5M) et si l'item n'est pas obtainable
        cash_value_str = item_data.get('Cash Value', '0')
        try:
            # Convertir la valeur en nombre (retirer tous les types d'espaces et convertir)
            if isinstance(cash_value_str, str):
                import re
                clean_cash_value_str = re.sub(r'[\s,\u00A0\u2000-\u200B\u202F\u205F\u3000]+', '', cash_value_str)
                if clean_cash_value_str.lower() in ['n/a', 'unknown', '']:
                    cash_value = 0
                else:
                    cash_value = int(clean_cash_value_str)
            else:
                cash_value = cash_value_str
        except (ValueError, TypeError):
            cash_value = 0

        # Vérifier si la valeur est >= 2.5M
        if cash_value < 2500000:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "<:ErrorLOGO:1387810170155040888> Item Rejected",
                f"The **{clean_item_name}** not has a value below 2.5M and can't be selected!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # For hyperchromes, we need to get the correct API data using the detected name
        if parsed_item.get('is_hyperchrome', False):
            # Get the actual API data for the detected hyperchrome
            api_name = parsed_item.get('api_name')
            if api_name and api_name in stockage_system.api_data:
                item_data = stockage_system.api_data[api_name]
                item_name = api_name  # Use the full API name for internal processing
            clean_item_name = parsed_item['name']  # But use the clean name for display
        else:
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

        # Get value based on status (case insensitive comparison)
        if status.lower() == "clean":
            value_key = 'Cash Value'
        else:  # dupe
            value_key = 'Duped Value'

        value_str = item_data.get(value_key, 'N/A')

        if value_str == 'N/A' or not value_str or value_str == "N/A":
            # For hyperchromes, show the clean name in error message
            display_name_for_error = clean_item_name if parsed_item.get('is_hyperchrome', False) else item_name
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "Value Not Available",
                f"No {status} value available for '{display_name_for_error}'!"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Check if item is worth less than 2.5M
        try:
            if isinstance(value_str, str):
                # Remove all types of spaces (normal, Unicode, etc.) and commas
                import re
                clean_value_str = re.sub(r'[\s,\u00A0\u2000-\u200B\u202F\u205F\u3000]+', '', value_str)
                if clean_value_str.lower() in ['n/a', 'unknown', '']:
                    value = 0
                else:
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

        # Determine the correct name and type for the item entry
        if parsed_item.get('is_hyperchrome', False):
            # For hyperchromes, use the clean name (without (HyperChrome) and without year)
            clean_name = parsed_item['name']
            # Remove year from display name (e.g., "HyperShift 2023" → "HyperShift")
            import re
            clean_name = re.sub(r'\s+\d{4}$', '', clean_name).strip()
            final_item_type = "HyperChrome"
        else:
            # For regular items, clean the name and extract type
            import re
            clean_name = re.sub(r'\s*\([^)]*\)$', '', item_name).strip()

            # Get item type from the full name
            type_match = re.search(r'\(([^)]*)\)', item_name)
            final_item_type = type_match.group(1) if type_match else "Unknown"

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

        # Save updated items list to state
        self.parent_view.ticket_system.save_ticket_state(interaction.channel.id, self.parent_view.user_id, {
            'items_list': self.parent_view.items_list
        })

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
            custom_id='payment_gamepass_persistent'
        )
        gamepass_button.callback = self.gamepass_method
        self.add_item(gamepass_button)

        # Group Donation Method button
        group_button = discord.ui.Button(
            label='Group Donation Method',
            style=discord.ButtonStyle.primary,
            emoji='<:GroupLOGO:1411125220873474179>',
            custom_id='payment_group_persistent'
        )
        group_button.callback = self.group_method
        self.add_item(group_button)

        # Information button
        info_button = discord.ui.Button(
            label='Information',
            style=discord.ButtonStyle.secondary,
            emoji='<:InformationLOGO:1410970300841066496>',
            custom_id='payment_info_persistent',
            row=1
        )
        info_button.callback = self.information
        self.add_item(info_button)

        # Back button (disabled if needed)
        back_button = discord.ui.Button(
            label='Back',
            style=discord.ButtonStyle.secondary,
            emoji='<:BackLOGO:1410726662328422410>',
            custom_id='payment_back_persistent',
            disabled=self.disable_back
        )
        back_button.callback = self.back_to_selling
        self.add_item(back_button)

    async def gamepass_method(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = UsernameModal(self, method="gamepass")
        await interaction.response.send_modal(modal)

    async def group_method(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        modal = UsernameModal(self, method="group")
        await interaction.response.send_modal(modal)

    async def information(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        user_id = state.get('user_id')
        items_list = state.get('items_list', [])

        # Save information state
        self.ticket_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'information',
            'items_list': items_list
        })

        info_embed = await self.ticket_system.create_information_embed(interaction.user)
        view = InformationView(self.ticket_system, user_id, items_list)
        await interaction.response.edit_message(embed=info_embed, view=view)

    async def back_to_selling(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        if self.disable_back:
            await interaction.response.send_message("This button is currently disabled.", ephemeral=True)
            return

        user_id = state.get('user_id')
        items_list = state.get('items_list', [])

        # Save selling state
        self.ticket_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'selling',
            'items_list': items_list
        })

        # Go back to selling form
        selling_embed = await self.ticket_system.create_selling_list_embed(interaction.user, items_list)
        view = SellingFormView(self.ticket_system, user_id, items_list)
        view.update_buttons()
        await interaction.response.edit_message(embed=selling_embed, view=view)

class InformationView(discord.ui.View):
    def __init__(self, ticket_system, user_id, items_list):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user_id = user_id
        self.items_list = items_list

    @discord.ui.button(label='Back', style=discord.ButtonStyle.secondary, emoji='<:BackLOGO:1410726662328422410>', custom_id='info_back_persistent')
    async def back_to_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        user_id = state.get('user_id')
        items_list = state.get('items_list', [])

        # Save payment method state
        self.ticket_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'payment_method',
            'items_list': items_list
        })

        payment_embed = await self.ticket_system.create_payment_method_embed(interaction.user, items_list)
        view = PaymentMethodView(self.ticket_system, user_id, items_list, disable_back=False)
        await interaction.response.edit_message(embed=payment_embed, view=view)

class UsernameModal(discord.ui.Modal):
    def __init__(self, parent_view, method="gamepass"):
        super().__init__(title="Roblox Username")
        self.parent_view = parent_view
        self.ticket_system = parent_view.ticket_system
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
                error_embed = await self.ticket_system.create_error_embed(
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

            # Save account confirmation state
            self.ticket_system.save_ticket_state(interaction.channel.id, self.parent_view.user_id, {
                'current_step': 'account_confirmation',
                'roblox_user_data': roblox_user_data,
                'payment_method': self.method
            })

            # Create account confirmation embed
            confirmation_embed = await self.ticket_system.create_account_confirmation_embed(roblox_user_data)

            # Create confirmation view
            confirmation_view = AccountConfirmationView(
                self.ticket_system,
                self.parent_view.user_id,
                self.parent_view.items_list,
                roblox_user_data,
                self.method
            )

            await interaction.edit_original_response(embed=confirmation_embed, view=confirmation_view)

        except ImportError:
            error_embed = await self.ticket_system.create_error_embed(
                "System Error",
                "Roblox integration is not available. Please contact an administrator."
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = await self.ticket_system.create_error_embed(
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

    @discord.ui.button(label='Confirm', emoji='<:ConfirmLOGO:1410970202191171797>', style=discord.ButtonStyle.success, custom_id='confirm_account_persistent')
    async def confirm_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        await interaction.response.defer()

        if self.method == "gamepass":
            await self._handle_gamepass_method(interaction)
        elif self.method == "group":
            await self._handle_group_method(interaction)

    @discord.ui.button(label='Other Account', style=discord.ButtonStyle.secondary, emoji='<:Update_LOGO:1411113397742997504>', custom_id='other_account_persistent')
    async def other_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Create a temporary PaymentMethodView to use as parent for the modal
        temp_parent = PaymentMethodView(self.ticket_system, self.user_id, self.items_list)
        modal = UsernameModal(temp_parent, self.method)
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

            # Save gamepass monitoring state
            monitoring_data = {
                'username': self.roblox_user_data['name'],
                'experience_id': universe_id,
                'expected_price': expected_price
            }
            self.ticket_system.save_ticket_state(interaction.channel.id, self.user_id, {
                'current_step': 'gamepass_monitoring',
                'monitoring_data': monitoring_data
            })

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

            # Disable buttons on current embed (confirmation embed)
            disabled_view = discord.ui.View()
            disabled_view.timeout = None

            # Add disabled buttons
            confirm_button = discord.ui.Button(
                label='Confirm',
                emoji= '<:ConfirmLOGO:1410970202191171797>',
                style=discord.ButtonStyle.success,
                custom_id='confirm_account_disabled',
                disabled=True
            )
            other_button = discord.ui.Button(
                label='Other Account',
                emoji='<:Update_LOGO:1411113397742997504>',
                style=discord.ButtonStyle.secondary,
                custom_id='other_account_disabled',
                disabled=True
            )

            disabled_view.add_item(confirm_button)
            disabled_view.add_item(other_button)

            # Update the current embed with disabled buttons
            await interaction.edit_original_response(view=disabled_view)

            if is_in_group:
                # User already in group - direct transaction
                transaction_embed = await self.ticket_system.create_group_transaction_embed(
                    interaction.user, self.items_list, total_robux,
                    self.roblox_user_data['name'], user_id
                )

                view = GroupTransactionView(
                    self.ticket_system, interaction.user, self.items_list,
                    total_robux, self.roblox_user_data['name']
                )

                # Send the embed with ping attached to the same message
                content = f"{interaction.user.mention} <@&1300798850788757564>"
                await interaction.followup.send(content=content, embed=transaction_embed, view=view)
            else:
                # User needs to join group - send new embed
                join_embed = await self.ticket_system.create_group_join_embed()
                await interaction.followup.send(embed=join_embed)

                # Save group monitoring state
                monitoring_data = {
                    'user_id': user_id,
                    'group_id': group_id,
                    'total_robux': total_robux,
                    'roblox_username': self.roblox_user_data['name']
                }
                self.ticket_system.save_ticket_state(interaction.channel.id, self.user_id, {
                    'current_step': 'group_monitoring',
                    'monitoring_data': monitoring_data
                })

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

class WaitingPeriodView(discord.ui.View):
    def __init__(self, ticket_system, user, items_list, total_robux, roblox_username, user_id, end_timestamp=None):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user = user
        self.items_list = items_list
        self.total_robux = total_robux
        self.roblox_username = roblox_username
        self.user_id = user_id
        self.end_timestamp = end_timestamp
        self.countdown_task = None
        
        # Start countdown if we have an end timestamp
        if self.end_timestamp:
            self.start_countdown_task()
    
    def start_countdown_task(self):
        """Start the countdown task that updates every second"""
        if self.countdown_task:
            self.countdown_task.cancel()
        self.countdown_task = asyncio.create_task(self._countdown_loop())
    
    async def _countdown_loop(self):
        """Countdown loop that updates every second and saves state"""
        import time
        
        try:
            while True:
                current_time = int(time.time())
                time_remaining = self.end_timestamp - current_time
                
                # Save current state every second
                if hasattr(self, '_last_channel'):
                    self.ticket_system.save_ticket_state(self._last_channel.id, self.user.id, {
                        'current_step': 'waiting_period',
                        'items_list': self.items_list,
                        'end_timestamp': self.end_timestamp,
                        'total_robux': self.total_robux,
                        'roblox_username': self.roblox_username,
                        'user_id': self.user_id,
                        'last_update': current_time
                    })
                
                if time_remaining <= 0:
                    # Time is up! Convert to transaction ready
                    if hasattr(self, '_last_message') and hasattr(self, '_last_channel'):
                        # Create transaction ready embed
                        transaction_embed = await self.ticket_system.create_group_transaction_embed(
                            self.user, self.items_list, self.total_robux, self.roblox_username, self.user_id
                        )
                        
                        # Create new view for transaction
                        view = GroupTransactionView(
                            self.ticket_system, self.user, self.items_list,
                            self.total_robux, self.roblox_username
                        )
                        
                        # Update message and ping support
                        await self._last_message.edit(embed=transaction_embed, view=view)
                        content = f"{self.user.mention} <@&1300798850788757564>"
                        await self._last_channel.send(content=content)
                    break
                
                # Update embed with new countdown
                if hasattr(self, '_last_message'):
                    try:
                        updated_embed = await self.ticket_system.create_waiting_period_embed(
                            self.roblox_username, self.end_timestamp
                        )
                        await self._last_message.edit(embed=updated_embed, view=self)
                    except discord.NotFound:
                        # Message was deleted
                        break
                    except Exception as e:
                        print(f"Error updating countdown: {e}")
                
                await asyncio.sleep(1)  # Update every second
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in countdown loop: {e}")
    
    def set_message_reference(self, message, channel):
        """Set reference to the message and channel for updates"""
        self._last_message = message
        self._last_channel = channel

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.success, emoji='<:ConfirmLOGO:1410970202191171797>', custom_id='confirm_waiting_period_persistent')
    async def confirm_waiting(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Create the group transaction embed
        transaction_embed = await self.ticket_system.create_group_transaction_embed(
            self.user, self.items_list, self.total_robux, self.roblox_username, self.user_id
        )

        view = GroupTransactionView(
            self.ticket_system, self.user, self.items_list,
            self.total_robux, self.roblox_username
        )

        content = f"{self.user.mention} <@&1300798850788757564>"
        await interaction.response.edit_message(embed=transaction_embed, view=view)
        await interaction.followup.send(content=content)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger, emoji='<:CloseLOGO:1411114868471496717>', custom_id='cancel_waiting_period_persistent')
    async def cancel_waiting(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Show cancel confirmation embed as a NEW message
        cancel_embed = await self.ticket_system.create_cancel_confirmation_embed()
        view = CancelConfirmationView(self.ticket_system, self.user)
        await interaction.response.send_message(embed=cancel_embed, view=view)

class CancelConfirmationView(discord.ui.View):
    def __init__(self, ticket_system, user):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user = user

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.danger, emoji='<:ConfirmLOGO:1410970202191171797>', custom_id='confirm_cancel_persistent')
    async def confirm_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Delete the channel and cleanup state
        channel_id = interaction.channel.id
        await interaction.response.defer()

        # Remove from active tickets and states
        user_id = str(self.user.id)
        if user_id in self.ticket_system.data['active_tickets']:
            del self.ticket_system.data['active_tickets'][user_id]
        self.ticket_system.remove_ticket_state(channel_id)

        await interaction.channel.delete(reason="Transaction cancelled by user")

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary, emoji='<:CloseLOGO:1411114868471496717>', custom_id='cancel_cancel_persistent')
    async def cancel_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Simply delete the message without notification
        await interaction.response.defer()
        await interaction.delete_original_response()

class GroupTransactionView(discord.ui.View):
    def __init__(self, ticket_system, user, items_list, total_robux, roblox_username):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.user = user
        self.items_list = items_list
        self.total_robux = total_robux
        self.roblox_username = roblox_username

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success, emoji='<:ConfirmLOGO:1410970202191171797>', custom_id='accept_group_transaction_persistent')
    async def accept_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get ticket state for validation
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state:
            await interaction.response.send_message("This ticket is no longer valid!", ephemeral=True)
            return

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

        # Send acceptance embed with user ping
        accept_embed = await self.ticket_system.create_selling_accepted_embed(self.user, interaction.channel.id)
        await interaction.response.send_message(content=self.user.mention, embed=accept_embed)

        # Disable the buttons
        self.clear_items()
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label='Refuse', style=discord.ButtonStyle.danger, emoji='<:CloseLOGO:1411114868471496717>', custom_id='refuse_group_transaction_persistent')
    async def refuse_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get ticket state for validation
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state:
            await interaction.response.send_message("This ticket is no longer valid!", ephemeral=True)
            return

        # Check if user has the required role
        required_role_id = 1300798850788757564
        if not any(role.id == required_role_id for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to refuse transactions!", ephemeral=True)
            return

        modal = RefuseReasonModal(self.user, interaction.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Information', emoji='<:InformationLOGO:1410970300841066496>', style=discord.ButtonStyle.secondary, custom_id='sell_info_group_persistent')
    async def sell_information(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get ticket state to retrieve items_list
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state:
            await interaction.response.send_message("This ticket is no longer valid!", ephemeral=True)
            return
            
        items_list = state.get('items_list', [])
        if not items_list:
            await interaction.response.send_message("No items found in this ticket!", ephemeral=True)
            return
            
        info_embed = await self.ticket_system.create_sell_info_embed(items_list)
        await interaction.response.send_message(embed=info_embed, ephemeral=True)

class RefuseReasonModal(discord.ui.Modal):
    def __init__(self, user, channel):
        super().__init__(title="Refuse Reason")
        self.user = user
        self.channel = channel

        self.reason = discord.ui.TextInput(
            label="Reason",
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
            title="<:ErrorLOGO:1387810170155040888> Request Refused",
            description=f"Your selling request has been refused by our staff for these reasons:\n{self.reason.value}",
            color=0xff0000
        )

        try:
            # Send DM to user
            await self.user.send(embed=refuse_embed)
        except discord.Forbidden:
            await interaction.followup.send("Could not send DM to user, But transaction was refused.", ephemeral=True)

        # Delete the channel after a short delay
        await asyncio.sleep(5)
        await self.channel.delete(reason="Transaction Refused by Staff")

class AcceptTransactionView(discord.ui.View):
    def __init__(self, ticket_system, channel, user):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.channel = channel
        self.user = user

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success, emoji='<:ConfirmLOGO:1410970202191171797>', custom_id='accept_transaction_persistent')
    async def accept_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get ticket state for validation
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state:
            await interaction.response.send_message("This ticket is no longer valid!", ephemeral=True)
            return

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

        # Send acceptance embed with user ping
        accept_embed = await self.ticket_system.create_selling_accepted_embed(self.user, self.channel.id)
        await interaction.response.send_message(content=self.user.mention, embed=accept_embed)

        # Disable the buttons
        self.clear_items()
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label='Refuse', style=discord.ButtonStyle.danger, emoji='<:CloseLOGO:1411114868471496717>', custom_id='refuse_gamepass_transaction_persistent')
    async def refuse_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get ticket state for validation
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state:
            await interaction.response.send_message("This ticket is no longer valid!", ephemeral=True)
            return

        # Check if user has the required role
        required_role_id = 1300798850788757564
        if not any(role.id == required_role_id for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to refuse transactions!", ephemeral=True)
            return

        modal = RefuseReasonModal(self.user, self.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Information', style=discord.ButtonStyle.secondary, emoji='<:InformationLOGO:1410970300841066496>', custom_id='gamepass_sell_info_persistent')
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
    bot.add_view(TicketOptionsView(ticket_system, 0))  # dummy user_id for persistence
    bot.add_view(SellingFormView(ticket_system, 0, []))  # dummy values for persistence
    bot.add_view(PaymentMethodView(ticket_system, 0, []))  # dummy values for persistence
    bot.add_view(InformationView(ticket_system, 0, []))  # dummy values for persistence
    bot.add_view(AccountConfirmationView(ticket_system, 0, [], {}, "gamepass"))  # dummy values for persistence
    bot.add_view(GroupTransactionView(ticket_system, None, [], 0, ""))  # dummy values for persistence
    bot.add_view(AcceptTransactionView(ticket_system, None, None))  # dummy values for persistence
    bot.add_view(WaitingPeriodView(ticket_system, None, [], 0, "", 0, None))  # dummy values for persistence
    bot.add_view(CancelConfirmationView(ticket_system, None))  # dummy values for persistence

    # Restore persistent views for existing tickets
    async def restore_persistent_views():
        await bot.wait_until_ready()
        try:
            # Create a copy of the dictionary to avoid "dictionary changed size during iteration" error
            ticket_states_copy = dict(ticket_system.data.get('ticket_states', {}))
            for channel_id_str, state in ticket_states_copy.items():
                try:
                    channel_id = int(channel_id_str)
                    channel = bot.get_channel(channel_id)
                    if channel:
                        user_id = state.get('user_id')
                        result = await ticket_system.restore_ticket_view(channel, user_id)
                        if result:
                            embed, view = result
                            # Find the last message in the channel and edit it
                            async for message in channel.history(limit=10):
                                if message.author == bot.user and message.embeds:
                                    try:
                                        await message.edit(embed=embed, view=view)
                                        print(f"Restored view for channel {channel_id}")
                                        break
                                    except discord.NotFound:
                                        # Message was deleted, skip
                                        continue
                                    except Exception as e:
                                        print(f"Error editing message in channel {channel_id}: {e}")
                                        continue
                    else:
                        # Channel doesn't exist anymore, clean up state
                        ticket_system.remove_ticket_state(channel_id)
                        print(f"Cleaned up state for non-existent channel {channel_id}")
                except Exception as e:
                    print(f"Error restoring view for channel {channel_id_str}: {e}")
        except Exception as e:
            print(f"Error in restore_persistent_views: {e}")

    # Run the restoration in the background
    bot.loop.create_task(restore_persistent_views())

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