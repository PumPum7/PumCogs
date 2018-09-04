import discord
from redbot.core import commands
from io import BytesIO
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageSequence, ImageColor
import aiohttp


class ImageEditing:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="blur")
    async def blur_images(self, ctx, url: str=None):
        # checks if any image was specified
        if url is None and len(ctx.message.attachments) < 1:
            return await ctx.send("Please supply an image.")
        msg = await ctx.send("⏱ I will now edit the image.")
        # gets an url if an attachment was used
        if url is None:
            attachment = ctx.message.attachments[0]
            url = attachment.url
        image = await self.edit_img(url, "BLUR")
        if image is not None:
            await ctx.send(file=image, content="Edited image:")
            await msg.delete()
        else:
            await msg.edit("Something didn't go quite right. Please make sure you used a valid image.")

    @staticmethod
    async def edit_img(url, method):
        methods = {'GAUSSIANBLUR': "GaussianBlur", 'MEDIANFILTER': "MedianFilter"}
        if method in methods:
            method = methods[method]
        if url.endswith(".gif"):
            return None
        try:
            # gets image
            async with aiohttp.ClientSession() as client_session:
                async with client_session.get(url) as response:
                    image_bytes = await response.read()
            # edits image
            with Image.open(BytesIO(image_bytes)) as image:
                image = image.filter(eval(f"ImageFilter.{method}"))
                output_buffer = BytesIO()
                image.save(output_buffer, "png")
                output_buffer.seek(0)
                image = discord.File(filename=f"{method}_edited.png", fp=output_buffer)
                return image
        except Exception as e:
            print(e)
            return None

    @commands.command(name="contour")
    async def contour_images(self, ctx, url: str=None):
        # checks if any image was specified
        if url is None and len(ctx.message.attachments) < 1:
            return await ctx.send("Please supply an image.")
        msg = await ctx.send("⏱ I will now edit the image.")
        # gets an url if an attachment was used
        if url is None:
            attachment = ctx.message.attachments[0]
            url = attachment.url
        image = await self.edit_img(url, "CONTOUR")
        if image is not None:
            await ctx.send(file=image, content="Edited image:")
            await msg.delete()
        else:
            await msg.edit("Something didn't go quite right. Please make sure you used a valid image.")

    @commands.command(name="edge_enhance")
    async def image_edge_enhance(self, ctx, url: str=None):
        # checks if any image was specified
        if url is None and len(ctx.message.attachments) < 1:
            return await ctx.send("Please supply an image.")
        msg = await ctx.send("⏱ I will now edit the image.")
        # gets an url if an attachment was used
        if url is None:
            attachment = ctx.message.attachments[0]
            url = attachment.url
        image = self.edit_img(url, "EDGE_ENHANCE_MORE")
        if image is not None:
            await ctx.send(file=image, content="Edited image:")
            await msg.delete()
        else:
            await msg.edit("Something didn't go quite right. Please make sure you used a valid image.")

    @commands.command(name="edit")
    async def emboss_image(self, ctx, url: str = None, method: str=None):
        # checks if any image was specified
        if url is None and len(ctx.message.attachments) < 1:
            return await ctx.send("Please supply an image.")
        methods = "BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE, EMBOSS, FIND_EDGES, SHARPEN, SMOOTH, " \
                  "SMOOTH_MORE, GaussianBlur, MedianFilter"
        if method is None:
            return await ctx.send(f"Please specify one of these methods: {methods.lower()}.")
        msg = await ctx.send("⏱ I will now edit the image.")
        # gets an url if an attachment was used
        if url is None:
            attachment = ctx.message.attachments[0]
            url = attachment.url
        image = await self.edit_img(url, method.upper())
        if image is not None:
            await ctx.send(file=image, content="Edited image:")
            await msg.delete()
        else:
            await msg.edit(content="Something didn't go quite right. Please make sure you used a valid image.")
