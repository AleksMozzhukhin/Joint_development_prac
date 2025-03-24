import asyncio
import shlex

async def echo(reader, writer):
    me = "{}:{}".format(*writer.get_extra_info('peername'))
    print(me)
    while data := await reader.readline():
        tmp=shlex.split(data.decode())
        if len(tmp)>1:
            if tmp[0].strip()=="print":
                writer.write((" ".join(tmp[0:])+'\n').encode())
            elif tmp[0].strip()=="info":
                if tmp[1].strip()=='host':
                    writer.write((writer.get_extra_info('peername')[0]+'\n').encode())
                elif tmp[1].strip()=='port':
                    writer.write((str(writer.get_extra_info('peername')[1])+'\n').encode())
                else:
                    writer.write(b"Undefined parameter\n")
            else:
                writer.write(b"Undefined function\n")
        else:
            writer.write(b'Empty request\n')
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(echo, '0.0.0.0', 1337)
    async with server:
        await server.serve_forever()

asyncio.run(main())