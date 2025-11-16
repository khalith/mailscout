import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.models.upload import Upload, UploadStatus

async def process_upload(upload: Upload, db: AsyncSession):
    print(f"Processing: {upload.id}")

    # Fake example: increment processed_count gradually
    for i in range(0, upload.total_count, 100):
        upload.processed_count = i
        upload.status = UploadStatus.processing
        await db.commit()
        await asyncio.sleep(1)

    upload.processed_count = upload.total_count
    upload.status = UploadStatus.completed
    await db.commit()

async def worker_loop():
    while True:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Upload).where(Upload.status == UploadStatus.queued)
            )
            jobs = result.scalars().all()

            for job in jobs:
                await process_upload(job, db)

        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(worker_loop())
