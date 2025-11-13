import os
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from django.utils import timezone

from apps.game.models import ProcessedBook
from apps.game.services import create_vector_store

logger = logging.getLogger("game.processor")


@dataclass
class PDFProcessor:
    """
    Processador de PDFs Fighting Fantasy para indexação no Weaviate.
    Adaptado para Django.
    """

    pdf_path: str
    class_name: str
    adventure_id: int
    chunk_size: int = 700
    chunk_overlap: int = 150
    batch_size: int = 20
    max_workers: int = 4
    chunks: List[Document] = field(default_factory=list)

    def __post_init__(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {self.pdf_path}")

        self.pdf_filename = os.path.basename(self.pdf_path)
        self.pdf_size = os.path.getsize(self.pdf_path)

        logger.info(f"PDFProcessor inicializado: {self.class_name}")

        # Verifica se já foi processado
        self.processed_book = ProcessedBook.objects.filter(
            weaviate_class_name=self.class_name
        ).first()

        if self.processed_book and self.processed_book.processing_status == "success":
            self.skip_processing = True
            logger.warning(f"Livro já processado: {self.class_name}")
        else:
            self.skip_processing = False
            self.weaviate_store = create_vector_store(self.class_name)

            if not self.weaviate_store:
                raise Exception(
                    f"Não foi possível criar vector store: {self.class_name}"
                )

    def extract_text(self) -> List[Document]:
        """Extrai texto do PDF usando PyMuPDF."""
        try:
            logger.info(f"Extraindo texto de: {self.pdf_filename}")
            documents = PyMuPDFLoader(self.pdf_path).load()
            logger.info(f"Extraídas {len(documents)} páginas")
            return documents
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}", exc_info=True)
            raise

    def split_text(self, documents: List[Document]) -> List[Document]:
        """
        Divide texto usando separadores específicos de Fighting Fantasy.
        """
        try:
            logger.info("Dividindo texto em chunks...")

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=[
                    r"(\d+)\n",  # Números de seção
                    r"\n\n",  # Parágrafos
                    r"\.",  # Sentenças
                    r"HABILIDADE|ENERGIA|SORTE",  # Stats
                    r"Teste sua|Role os dados",  # Testes
                    r"\n",  # Linhas
                    r"\s+",  # Espaços
                    r"(?<=\S)(?=[A-Z])",  # Mudança de palavra maiúscula
                ],
                keep_separator=True,
            )

            chunks = splitter.split_documents(documents)
            logger.info(f"Criados {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Erro ao dividir texto: {e}", exc_info=True)
            raise

    def process_pdf(self) -> List[Document]:
        """Processa o PDF completo."""
        if self.skip_processing:
            logger.warning("Processamento pulado: já processado anteriormente")
            return []

        documents = self.extract_text()
        self.chunks = self.split_text(documents)
        return self.chunks

    def _process_batch(
        self, batch: List[Document], batch_num: int, total_batches: int
    ) -> bool:
        """Processa um lote de chunks e indexa no Weaviate."""
        try:
            logger.info(f"Processando lote {batch_num}/{total_batches}")

            batch_with_metadata = [
                Document(
                    page_content=chunk.page_content,
                    metadata={
                        "source": self.class_name,
                        "adventure_id": self.adventure_id,
                        "batch": batch_num,
                        "page": chunk.metadata.get("page", 0),
                        "total_pages": len(
                            set(doc.metadata.get("page", 0) for doc in self.chunks)
                        ),
                    },
                )
                for chunk in batch
            ]

            self.weaviate_store.add_documents(batch_with_metadata)
            logger.info(f"Lote {batch_num}/{total_batches} indexado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao indexar lote {batch_num}: {e}", exc_info=True)
            return False

    def index_in_weaviate(self) -> Dict[str, Any]:
        """Indexa todos os chunks no Weaviate usando threads."""
        if not self.chunks:
            return {"success": False, "indexed": 0, "total": 0}

        total_batches = (len(self.chunks) + self.batch_size - 1) // self.batch_size
        success_count = 0

        logger.info(f"Iniciando indexação: {total_batches} lotes")

        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, total_batches)
        ) as executor:
            future_to_batch = {
                executor.submit(
                    self._process_batch,
                    self.chunks[i : i + self.batch_size],
                    (i // self.batch_size) + 1,
                    total_batches,
                ): (i // self.batch_size)
                + 1
                for i in range(0, len(self.chunks), self.batch_size)
            }

            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    if future.result():
                        success_count += 1
                except Exception as e:
                    logger.error(f"Erro no processamento do lote {batch_num}: {e}")

        return {
            "success": success_count == total_batches,
            "indexed": success_count,
            "total": total_batches,
            "documents": len(self.chunks),
        }

    def run(self) -> Dict[str, Any]:
        """
        Executa o processamento completo do PDF.

        Returns:
            dict com resultado do processamento
        """
        try:
            if self.skip_processing:
                return {
                    "status": "skipped",
                    "message": "PDF já processado anteriormente",
                    "class_name": self.class_name,
                }

            # Cria ou atualiza registro ProcessedBook
            processed_book, created = ProcessedBook.objects.get_or_create(
                adventure_id=self.adventure_id,
                defaults={
                    "weaviate_class_name": self.class_name,
                    "pdf_filename": self.pdf_filename,
                    "pdf_size_bytes": self.pdf_size,
                    "processing_status": "processing",
                    "processing_started_at": timezone.now(),
                },
            )

            if not created:
                processed_book.processing_status = "processing"
                processed_book.processing_started_at = timezone.now()
                processed_book.save()

            # Processa PDF
            self.process_pdf()

            # Indexa no Weaviate
            stats = self.index_in_weaviate()

            # Atualiza status
            if stats["success"]:
                processed_book.processing_status = "success"
            elif stats["indexed"] > 0:
                processed_book.processing_status = "partial"
            else:
                processed_book.processing_status = "error"
                processed_book.error_message = "Nenhum chunk indexado"

            processed_book.chunks_extracted = len(self.chunks)
            processed_book.chunks_indexed = stats["indexed"] * self.batch_size
            processed_book.processing_completed_at = timezone.now()
            processed_book.save()

            logger.info(
                f"Processamento concluído: {self.class_name} - "
                f"Status: {processed_book.processing_status}"
            )

            return {
                "status": processed_book.processing_status,
                "pdf_path": self.pdf_path,
                "class_name": self.class_name,
                "chunks_extracted": len(self.chunks),
                "indexing_stats": stats,
            }

        except Exception as e:
            logger.error(
                f"Erro no processamento do PDF {self.pdf_path}: {e}", exc_info=True
            )

            # Atualiza status de erro
            if hasattr(self, "processed_book"):
                processed_book.processing_status = "error"
                processed_book.error_message = str(e)
                processed_book.processing_completed_at = timezone.now()
                processed_book.save()

            return {
                "status": "error",
                "pdf_path": self.pdf_path,
                "error": str(e),
            }


def process_book_upload(
    pdf_path: str, class_name: str, adventure_id: int
) -> Dict[str, Any]:
    """
    Função helper para processar upload de livro.

    Args:
        pdf_path: Caminho do arquivo PDF
        class_name: Nome da classe Weaviate
        adventure_id: ID da aventura

    Returns:
        Resultado do processamento
    """
    processor = PDFProcessor(
        pdf_path=pdf_path, class_name=class_name, adventure_id=adventure_id
    )

    return processor.run()
