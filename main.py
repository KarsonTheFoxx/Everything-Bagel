from asyncio import run

async def main(TOKEN):
    from disnake.ext import commands
    from disnake import Intents, Status, Activity, ActivityType, CommandInteraction, Embed, Color, ui, ButtonStyle, MessageInteraction
    from os import listdir

    intents = Intents.default()
    intents.members = True
    intents.message_content = True

    bot = commands.AutoShardedInteractionBot(intents=intents)

    @bot.event
    async def on_ready():
        await bot.change_presence(status=Status.idle, activity=Activity(name="�", type=ActivityType.watching))
        print(f"Ready; Logged in as {bot.user.name}")

    bot.load_extensions("extensions/")

    async def extensions_autocomplete(inter, text):
        return [extension[:-3].lower() for extension in listdir("extensions/") if extension.endswith(".py") and text.lower() in extension.lower()]

    @bot.slash_command(name="extensions", description="Management command to load/reload/unload extensions")
    async def extensions(inter:CommandInteraction, mode=commands.Param(choices=["load", "unload", "reload"]), extension=commands.Param(autocomplete=extensions_autocomplete)):
        try:
            match mode:
                case "load":
                    bot.load_extension(f"extensions/{extension}")
                case "unload":
                    bot.load_extension(f"extensions/{extension}")
                case "reload":
                    bot.unload_extension(f"extensions/{extension}")
                    bot.load(f"extensions/{extension}")
                case _:
                    raise ValueError("Unknown mode")

            await inter.response.send_message(embed=Embed(title=f"Extension {mode}ed", color=Color.green()), ephemeral=True)
        except Exception as error:
            button = ui.Button(style=ButtonStyle.green, label="Send traceback")
            view = ui.View()

            async def button_callback(inter:MessageInteraction):
                try:
                    await inter.author.send(f"```\n{error.with_traceback}\n```")
                except Exception:
                    await inter.followup.send(f"Failed to DM traceback\n```{error.with_traceback}\n```", ephemeral=True)

            button.callback = button_callback
            view.add_item(button)
            await inter.response.send_message(embed=Embed(title="Failed to proccess operation", description=str(error)), view=view, ephemeral=True)

    await bot.start(token=TOKEN)

if __name__ == '__main__':
    run(main(TOKEN=open("token.txt", 'r').read()))