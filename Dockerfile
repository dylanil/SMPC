FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py ./
COPY public ./public

# Drop privileges: a hypothetical container escape now starts from an
# unprivileged shell rather than uid 0. Defence in depth — doesn't stop
# bugs, just shrinks the blast radius if a chain of exploits ever lets
# an attacker run shell commands inside the container.
RUN useradd --system --uid 1000 --no-create-home app && chown -R app /app
USER app

ENV HOST=0.0.0.0
ENV PORT=8765
EXPOSE 8765

CMD ["python", "-u", "server.py"]
