
import discord
import json
import asyncio
from datetime import datetime
import re

class SellingTicketSystem:
    def __init__(self, bot, trading_system):
        self.bot = bot
        self.trading_system = trading_system
        
    async def handle_selling_option(self, interaction, user_id):
        """Handle the selling option from the main ticket system"""
        # Update channel name to selling type
        await self.trading_system.update_channel_type(interaction.channel, interaction.user, 'selling')

        # Save selling state
        self.trading_system.save_ticket_state(interaction.channel.id, user_id, {
            'current_step': 'selling',
            'items_list': []
        })

        # Create selling embed
        selling_embed = await self.trading_system.create_selling_embed(interaction.user)

        # Create selling form view
        selling_view = SellingFormView(self.trading_system, user_id, [])

        # Update the message with selling embed and form buttons
        await interaction.response.edit_message(embed=selling_embed, view=selling_view)

        # Notify support team
        support_roles = self.trading_system.get_support_roles(interaction.guild)
        if support_roles:
            role_mentions = " ".join([role.mention for role in support_roles])
            await interaction.followup.send(f"🔔 {role_mentions} New selling ticket created by {interaction.user.mention}!")

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

        # Update items_list from state before opening modal
        self.items_list = state.get('items_list', [])

        modal = ItemModal(self, "add")
        await interaction.response.send_modal(modal)

    async def handle_remove_item(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        # Update items_list from state before opening modal
        self.items_list = state.get('items_list', [])

        modal = ItemModal(self, "remove")
        await interaction.response.send_modal(modal)

    async def handle_next_to_payment(self, interaction: discord.Interaction):
        # Get user_id from ticket state since we can't store it in custom_id
        state = self.ticket_system.get_ticket_state(interaction.channel.id)
        if not state or interaction.user.id != state.get('user_id'):
            await interaction.response.send_message("Only the ticket creator can use this button!", ephemeral=True)
            return

        user_id = state.get('user_id')
        # Use the current view's items_list which is most up-to-date
        items_list = self.items_list

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
        from trading_ticket_system import TicketOptionsView
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

        # Use the neutral item matching system from ticket_system
        best_match, error_message = self.parent_view.ticket_system.find_best_item_match(self.item_name.value.strip())

        if not best_match:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "<:ErrorLOGO:1387810170155040888> Item Not Found",
                error_message
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        item_name, item_data = best_match[0], best_match[1]
        parsed_item = self.parent_view.ticket_system.parse_item_with_hyperchrome(self.item_name.value.strip())

        # Determine clean item name
        if parsed_item.get('is_hyperchrome', False):
            clean_item_name = parsed_item['name']
        else:
            clean_item_name = item_name.split('(')[0].strip()

        # Validate item requirements
        is_valid, validation_error = self.parent_view.ticket_system.validate_item_requirements(
            item_name, item_data, clean_item_name
        )

        if not is_valid:
            error_embed = await self.parent_view.ticket_system.create_error_embed(
                "<:ErrorLOGO:1387810170155040888> Item Rejected",
                validation_error
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Handle hyperchrome data setup
        if parsed_item.get('is_hyperchrome', False):
            # Get the actual API data for the detected hyperchrome
            from stockage_system import StockageSystem
            stockage_system = StockageSystem()
            api_name = parsed_item.get('api_name')
            if api_name and api_name in stockage_system.api_data:
                item_data = stockage_system.api_data[api_name]
                item_name = api_name  # Use the full API name for internal processing
            clean_item_name = parsed_item['name']  # But use the clean name for display
        else:
            clean_item_name = item_name.split('(')[0].strip()

            # Get item type from the full name
            import re
            type_match = re.search(r'\(([^)]*)\)', item_name)
            final_item_type = type_match.group(1) if type_match else "Unknown"

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
            # Check if item is in exceptions list (protected items)
            exceptions = self.parent_view.ticket_system.data.get('exceptions', [])
            full_item_name = f"{clean_name} ({final_item_type})"

            if full_item_name in exceptions:
                error_embed = await self.parent_view.ticket_system.create_error_embed(
                    "<:ErrorLOGO:1387810170155040888> Protected Item",
                    f"The **{clean_name}** is a protected item and cannot be removed from your list!"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
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

        # Save updated items list to state FIRST
        self.parent_view.ticket_system.save_ticket_state(interaction.channel.id, self.parent_view.user_id, {
            'items_list': self.parent_view.items_list
        })

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

            # Save account confirmation state with creator info preserved
            current_state = self.ticket_system.get_ticket_state(interaction.channel.id)
            creator_info = {}
            if current_state:
                creator_info = {
                    'creator_username': current_state.get('creator_username'),
                    'creator_display_name': current_state.get('creator_display_name')
                }

            self.ticket_system.save_ticket_state(interaction.channel.id, self.parent_view.user_id, {
                'current_step': 'account_confirmation',
                'roblox_user_data': roblox_user_data,
                'payment_method': self.method,
                **creator_info
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

# Importer les classes restantes depuis l'ancien fichier
from trading_ticket_system import (
    WaitingPeriodView, CancelConfirmationView, GroupTransactionView, 
    RefuseReasonModal, AcceptTransactionView
)
