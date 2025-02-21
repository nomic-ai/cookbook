import email.parser
from pathlib import Path
import pyarrow as pa
from pyarrow import parquet as pq, compute as pc, feather, ipc
from collections import Counter
import random
import tarfile

# The enron email dataset can be downloaded from a CMU-hosted site:
# https://www.cs.cmu.edu/~enron/

# Wherever you place the zip file, change this path to that.
ZIP_FILE_PATH = "~/Downloads/enron_mail_20150507.tar.gz"


# This function parses and iterates over all the e-mails. Here we're being careful to
# capture information about the tree structure--whose e-mail is each file from? What folder are
# they storing it? Reading directly out of the tarfile is faster than decompressing first into
# many little files, so that's what we'll do.
#
# Note that these e-mails are from 2001, so we parse them as Latin-1. (There are a few names
# from Eastern Europe that use the Latin-1 versions of characters like 'ä' in them.)
def all_emails():
    parser = email.parser.Parser()

    with tarfile.open(Path(ZIP_FILE_PATH).expanduser(), "r:gz") as tf:
        for member in tf.getmembers():
            if member.isdir():
                # Not directories
                continue
            f = tf.extractfile(member)
            if f is None:
                continue
            txt = f.read().decode("latin-1")
            msg = parser.parsestr(txt)
            _, user, *folders = Path(member.name).parent.parts
            folder = "/".join(folders)
            yield user, folder, member.name, msg


# This function parses the information that comes out of the tarfile into a python dict.
# We want not just the headers, but also the e-mail body and the information about folder structure.
def email_to_dict(user, folder, filename, msg):
    metadata = dict(msg)
    text = msg.get_payload()
    return dict(_user=user, _folder=folder, _filename=filename, _text=text, **metadata)


# This function reads each buffer into a batch of 10,000 e-mails and adds a date column
# that properly parses the date string, in addition to the "Date" string.
def supplement_batch(buffer, schema):

    batch = pa.Table.from_pylist(buffer, schema)
    dates = pc.strptime(
        pc.utf8_slice_codeunits(batch["Date"], 0, 24),
        format="%a, %d %b %Y %H:%M:%S",
        unit="s",
    )
    # Timezones are the worst. This line is removing an all-null date field:
    # Adding in the UTC time that we parsed in the line above: and then
    # casting that globally to Houston time because as an Enron corpus that's
    # the most useful overall timezone to use. We could also preserve the TZ of the
    # original message, but we'll just leave that as part of the text
    # version.
    return batch.drop(["timestamp"]).append_column("timestamp", dates)


# This function gets the most common metadata fields from a random sample of 10,000 e-mails.
# By default we aren't using it because it's slow, and instead have just placed the results below.
def get_most_common_metadata():
    counter = Counter()

    buffer = [None] * 10_000
    for i, (dir, foldern, docno, msg) in enumerate(all_emails()):
        destination_position = None
        if i < len(buffer):
            destination_position = i
        else:
            destination_position = random.randint(0, i)
        message = email_to_dict(dir, foldern, docno, msg)
        counter.update(message.keys())
        if destination_position < len(buffer):
            buffer[destination_position] = message.keys()
        print(i, end="\r")

    return counter.most_common(21)


# The extracted metadata from the above function.
most_common_metadata = [
    {"_user": 517401},
    {"_folder": 517401},
    {"_filename": 517401},
    {"_text": 517401},
    {"Message-ID": 517401},
    {"Date": 517401},
    {"From": 517401},
    {"Subject": 517401},
    {"Mime-Version": 517372},
    {"Content-Type": 517372},
    {"Content-Transfer-Encoding": 517372},
    {"X-From": 517372},
    {"X-To": 517372},
    {"X-cc": 517372},
    {"X-bcc": 517372},
    {"X-Folder": 517372},
    {"X-Origin": 517372},
    {"X-FileName": 517372},
    {"To": 495554},
    {"Cc": 127881},
    {"Bcc": 127881},
]

# The schema for the Arrow file.
schema = pa.schema(
    {
        "_user": pa.string(),
        "_folder": pa.string(),
        "_filename": pa.string(),
        "_text": pa.string(),
        # If you want to run the metadata extractor, switch the lines below:
        **{[*k.keys()][0]: pa.string() for k in most_common_metadata},
        # **{[*k.keys()][0]: pa.string() for k, v in get_most_common_metadata()},
        "timestamp": pa.timestamp("s"),
    }
)

# This is the actual writing of the Arrow file
writer = ipc.new_file("emails.arrow", schema)
buffer = []
for i, (dir, foldern, docno, msg) in enumerate(all_emails()):
    destination_position = None
    message = email_to_dict(dir, foldern, docno, msg)
    buffer.append(message)
    if len(buffer) == 10_000:
        batch = supplement_batch(buffer, schema)
        writer.write_table(batch)
        buffer = []
    print(i, end="\r")
writer.close()

# Now we read the Arrow file back in and write out the Parquet version.
# The parquet file will be much smaller, and can be read by duckdb.
tb = feather.read_table("emails.arrow")

with pq.ParquetWriter(
    "emails.parquet", schema, compression="zstd", compression_level=9
) as writer:
    writer.write_table(tb)
