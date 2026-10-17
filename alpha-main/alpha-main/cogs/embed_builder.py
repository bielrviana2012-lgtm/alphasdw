
"""Comando administrativo para criar painéis personalizados com Components V2."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("Sr.Alpha.EmbedBuilder")


class EmbedBuilder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="criar_embed",
        description="Cria um painel personalizado com até 25 campos.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        titulo="Título que aparecerá no painel",
        descricao="Texto principal do painel",
        canal="Canal onde o painel será publicado",
        cor="Cor hexadecimal, por exemplo #9167FF",
        campos=(
            "Um campo por linha, no formato Título | Texto. "
            "Máximo de 25 campos."
        ),
    )
    async def criar_embed(
        self,
        interaction: discord.Interaction,
        titulo: app_commands.Range[str, 1, 200],
        descricao: app_commands.Range[str, 1, 3500],
        canal: discord.TextChannel,
        cor: app_commands.Range[str, 4, 7] = "#9167FF",
        campos: app_commands.Range[str, 1, 6000] = "",
    ):
        # Verifica o servidor e as permissões.
        if (
            not interaction.guild
            or not isinstance(interaction.user, discord.Member)
        ):
            await interaction.response.send_message(
                "Este comando só pode ser usado dentro de um servidor.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Apenas administradores podem criar painéis.",
                ephemeral=True,
            )
            return

        bot_member = interaction.guild.me

        if (
            bot_member is None
            or not canal.permissions_for(bot_member).send_messages
        ):
            await interaction.response.send_message(
                f"Não tenho permissão para enviar mensagens em {canal.mention}.",
                ephemeral=True,
            )
            return

        # Valida a cor hexadecimal.
        hex_color = cor.strip().removeprefix("#")

        if (
            len(hex_color) not in (3, 6)
            or any(
                char not in "0123456789abcdefABCDEF"
                for char in hex_color
            )
        ):
            await interaction.response.send_message(
                "Cor inválida. Use um código como #9167FF.",
                ephemeral=True,
            )
            return

        if len(hex_color) == 3:
            hex_color = "".join(char * 2 for char in hex_color)

        accent = discord.Color(int(hex_color, 16))

        # Lê os campos no formato Título | Texto.
        fields = []

        for linha in campos.splitlines():
            linha = linha.strip()

            if not linha:
                continue

            if "|" not in linha:
                await interaction.response.send_message(
                    f"Campo inválido: `{linha[:100]}`.\n"
                    "Use o formato `Título | Texto`, com um campo por linha.",
                    ephemeral=True,
                )
                return

            field_title, field_text = linha.split("|", 1)
            field_title = field_title.strip()
            field_text = field_text.strip()

            if not field_title or not field_text:
                await interaction.response.send_message(
                    "Todos os campos precisam ter título e texto.",
                    ephemeral=True,
                )
                return

            if len(field_title) > 256:
                await interaction.response.send_message(
                    "Cada título de campo pode ter no máximo 256 caracteres.",
                    ephemeral=True,
                )
                return

            if len(field_text) > 1000:
                await interaction.response.send_message(
                    "Cada texto de campo pode ter no máximo 1000 caracteres.",
                    ephemeral=True,
                )
                return

            fields.append((field_title, field_text))

            if len(fields) > 25:
                await interaction.response.send_message(
                    "Você pode adicionar no máximo 25 campos.",
                    ephemeral=True,
                )
                return

        # Monta o painel usando Components V2.
        layout = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container(accent_colour=accent)

        container.add_item(
            discord.ui.TextDisplay(f"# {titulo}")
        )
        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.TextDisplay(descricao)
        )

        for field_title, field_text in fields:
            container.add_item(
                discord.ui.TextDisplay(
                    f"**{field_title}**\n{field_text}"
                )
            )

        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.TextDisplay("-# Sr.Alpha • Family Alpha")
        )

        layout.add_item(container)

        await interaction.response.defer(
            ephemeral=True,
            thinking=True,
        )

        try:
            await canal.send(
                view=layout,
                allowed_mentions=discord.AllowedMentions.none(),
            )

            await interaction.followup.send(
                f"✅ Painel publicado em {canal.mention} "
                f"com {len(fields)} campo(s).",
                ephemeral=True,
            )

            log.info(
                "Painel publicado por %s em #%s (%s), com %s campos.",
                interaction.user,
                canal.name,
                canal.id,
                len(fields),
            )

        except discord.Forbidden:
            await interaction.followup.send(
                f"Não tenho permissão para publicar em {canal.mention}.",
                ephemeral=True,
            )

        except discord.HTTPException:
            log.exception("Falha ao publicar painel Components V2.")

            await interaction.followup.send(
                "Não consegui publicar o painel. Confira as permissões "
                "do bot e tente novamente.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedBuilder(bot))
