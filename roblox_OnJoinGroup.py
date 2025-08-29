
import asyncio
import time
from roblox_sync import RobloxClient

class GroupJoinMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.monitoring_tasks = {}
        self.client = RobloxClient()

    async def start_group_monitoring(self, channel, user, user_id, group_id, items_list, total_robux, roblox_username, ticket_system):
        """Start monitoring for group join"""
        task_key = f"{channel.id}_{user.id}"
        if task_key in self.monitoring_tasks:
            self.monitoring_tasks[task_key].cancel()

        self.monitoring_tasks[task_key] = asyncio.create_task(
            self._monitor_group_join(channel, user, user_id, group_id, items_list, total_robux, roblox_username, ticket_system)
        )

    async def _monitor_group_join(self, channel, user, user_id, group_id, items_list, total_robux, roblox_username, ticket_system):
        """Monitor for user joining the group"""
        try:
            while True:
                await asyncio.sleep(10)  # Check every 10 seconds

                if self.client.is_user_in_group(user_id, group_id):
                    # User joined! Show waiting period
                    end_timestamp = int(time.time()) + (14 * 24 * 60 * 60)  # 14 days from now

                    waiting_embed = await ticket_system.create_waiting_period_embed(
                        roblox_username, end_timestamp
                    )

                    await channel.send(embed=waiting_embed)

                    # Start timer for 2 weeks and setup completion callback
                    await self._setup_waiting_period(channel, user, items_list, total_robux, end_timestamp, ticket_system)
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error monitoring group join: {e}")

    async def _setup_waiting_period(self, channel, user, items_list, total_robux, end_timestamp, ticket_system):
        """Setup the 2-week waiting period"""
        try:
            current_time = int(time.time())
            wait_time = end_timestamp - current_time

            # Wait for the specified duration
            await asyncio.sleep(wait_time)

            # Send ready embed
            ready_embed = await ticket_system.create_transaction_ready_embed(
                items_list, total_robux
            )

            content = f"{user.mention} <@&1300798850788757564>"
            await channel.send(content=content, embed=ready_embed)

            # Allow user to speak
            overwrites = channel.overwrites
            if user in overwrites:
                overwrites[user].send_messages = True
                await channel.edit(overwrites=overwrites)

        except Exception as e:
            print(f"Error in waiting period setup: {e}")

    def cancel_monitoring(self, channel_id, user_id):
        """Cancel monitoring for a specific task"""
        task_key = f"{channel_id}_{user_id}"
        if task_key in self.monitoring_tasks:
            self.monitoring_tasks[task_key].cancel()
            del self.monitoring_tasks[task_key]

# Global instance
group_monitor = None

def setup_group_monitor(bot):
    """Setup function to create the group monitor"""
    global group_monitor
    group_monitor = GroupJoinMonitor(bot)
    return group_monitor
