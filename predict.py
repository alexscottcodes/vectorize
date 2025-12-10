from cog import BasePredictor, Input, Path
from PIL import Image
import subprocess
import tempfile
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
import time

console = Console()


class Predictor(BasePredictor):
    def setup(self):
        """Load the model into memory and perform any setup"""
        console.print(
            Panel.fit(
                "[bold cyan]🎨 Image Vectorizer Initialized[/bold cyan]\n"
                "Ready to convert raster images to beautiful SVG vectors!",
                border_style="cyan"
            )
        )

    def predict(
        self,
        image: Path = Input(
            description="Input raster image (PNG, JPG, etc.)",
        ),
        color_mode: str = Input(
            description="Color processing mode",
            choices=["color", "binary"],
            default="color"
        ),
        hierarchical: str = Input(
            description="Hierarchical clustering mode",
            choices=["stacked", "cutout"],
            default="stacked"
        ),
        filter_speckle: int = Input(
            description="Remove speckles smaller than this size (0-100)",
            default=4,
            ge=0,
            le=100
        ),
        color_precision: int = Input(
            description="Color precision/number of colors (1-8, lower = fewer colors)",
            default=6,
            ge=1,
            le=8
        ),
        layer_difference: int = Input(
            description="Layer difference threshold (0-100, higher = fewer layers)",
            default=16,
            ge=0,
            le=100
        ),
        corner_threshold: int = Input(
            description="Corner detection threshold (0-180 degrees)",
            default=60,
            ge=0,
            le=180
        ),
        segment_length: float = Input(
            description="Segment length for curve approximation",
            default=10.0,
            ge=3.5,
            le=50.0
        ),
        splice_threshold: int = Input(
            description="Splice threshold for curve simplification (0-180 degrees)",
            default=45,
            ge=0,
            le=180
        ),
    ) -> Path:
        """Vectorize a raster image to SVG format"""
        
        start_time = time.time()
        
        # Display input information
        console.print("\n[bold green]📥 Processing Input Image[/bold green]")
        
        # Load and analyze image
        img = Image.open(str(image))
        img_info = Table(show_header=False, box=None, padding=(0, 2))
        img_info.add_row("[cyan]Format:[/cyan]", str(img.format))
        img_info.add_row("[cyan]Size:[/cyan]", f"{img.size[0]} × {img.size[1]} pixels")
        img_info.add_row("[cyan]Mode:[/cyan]", img.mode)
        
        file_size = os.path.getsize(str(image))
        img_info.add_row("[cyan]File Size:[/cyan]", f"{file_size / 1024:.2f} KB")
        console.print(img_info)
        
        # Display vectorization settings
        console.print("\n[bold yellow]⚙️  Vectorization Settings[/bold yellow]")
        settings = Table(show_header=False, box=None, padding=(0, 2))
        settings.add_row("[cyan]Color Mode:[/cyan]", color_mode)
        settings.add_row("[cyan]Hierarchical:[/cyan]", hierarchical)
        settings.add_row("[cyan]Filter Speckle:[/cyan]", str(filter_speckle))
        settings.add_row("[cyan]Color Precision:[/cyan]", str(color_precision))
        settings.add_row("[cyan]Layer Difference:[/cyan]", str(layer_difference))
        console.print(settings)
        
        # Create output path
        output_path = Path(tempfile.mktemp(suffix=".svg"))
        
        # Build vtracer command
        cmd = [
            "vtracer",
            "--input", str(image),
            "--output", str(output_path),
            "--colormode", color_mode,
            "--hierarchical", hierarchical,
            "--filter_speckle", str(filter_speckle),
            "--color_precision", str(color_precision),
            "--layer_difference", str(layer_difference),
            "--corner_threshold", str(corner_threshold),
            "--length_threshold", str(segment_length),
            "--splice_threshold", str(splice_threshold),
        ]
        
        # Run vectorization with progress indicator
        console.print("\n[bold magenta]🔄 Vectorizing Image[/bold magenta]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Converting raster to vector...",
                total=100
            )
            
            # Simulate progress while processing
            progress.update(task, advance=20)
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                progress.update(task, advance=80)
                
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]❌ Error during vectorization:[/bold red]")
                console.print(f"[red]{e.stderr}[/red]")
                raise
        
        # Calculate metrics
        elapsed_time = time.time() - start_time
        output_size = os.path.getsize(str(output_path))
        compression_ratio = (1 - output_size / file_size) * 100 if file_size > 0 else 0
        
        # Display results
        console.print("\n[bold green]✅ Vectorization Complete![/bold green]")
        
        results = Table(show_header=False, box=None, padding=(0, 2))
        results.add_row("[cyan]Output Format:[/cyan]", "SVG (Scalable Vector Graphics)")
        results.add_row("[cyan]Output Size:[/cyan]", f"{output_size / 1024:.2f} KB")
        results.add_row(
            "[cyan]Size Change:[/cyan]",
            f"[{'green' if compression_ratio > 0 else 'red'}]{compression_ratio:+.1f}%[/]"
        )
        results.add_row("[cyan]Processing Time:[/cyan]", f"{elapsed_time:.2f} seconds")
        results.add_row("[cyan]Speed:[/cyan]", f"{(img.size[0] * img.size[1]) / elapsed_time / 1000:.1f}K pixels/sec")
        
        console.print(results)
        
        console.print(
            Panel.fit(
                "[bold green]🎉 Vector image ready for download![/bold green]\n"
                "Your image is now infinitely scalable without quality loss!",
                border_style="green"
            )
        )
        
        return output_path