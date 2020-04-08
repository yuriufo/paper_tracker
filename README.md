# paper_tracker
arxiv, google scholar, microsoft academic

## install

环境: `Python 3.7x`

```bash
$ git clone https://github.com/yuriufo/paper_tracker.git
$ cd ./paper_tracker
$ pip install -r requirements.txt
```
## datasets

### create

```bash
$ flask initdb
```

### update or recreate

```bash
$ flask initdb --drop
```

## run

```bash
$ flask run --host 0.0.0.0 --port 7777
```