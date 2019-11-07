import { Types, GameObjects, Scene } from 'phaser';
import { Cell } from '../models/cell';
import { GameMaster } from '../game-master';

const sceneConfig: Types.Scenes.SettingsConfig = {
    active: false,
    visible: false,
    key: 'attack',
};

export class AttackScene extends Scene {
    private gameMaster: GameMaster = GameMaster.instance;
    private grid: IGridElement[][];
    private clickPosition: { x: number, y: number };
    private dimensions: { width: number, height: number };

    constructor() {
        super(sceneConfig);
    }

    public async create(): Promise<void> {

        const board = await this.gameMaster.getOponentBoard();

        this.dimensions = board.dimensions;

        this.grid = board.map((cell: Cell, x: number, y: number) => {
            const rectangle = this.add.rectangle(0, 0, 0, 0, 0x0000FF, 0.4);
            rectangle
                .on('pointerdown', () => this.clickPosition = { x, y })
                .on('pointerup', () => this.clickGrid(x, y))
                .on('pointermove', () => this.hoverGrid(x, y))
                .on('pointerout', () => this.leaveGrid(x, y));
            return { rectangle, cell };
        });

        this.gameMaster.cellRevealed.on("oponent", cell => this.revealTile(cell));

        this.scale.on('resize', (gameSize: GameObjects.Components.Size) => this.resizeGrid(gameSize.width, gameSize.height));
        this.resizeGrid(window.innerWidth, window.innerHeight);
    }

    private resizeGrid(width: number, height: number): void {
        const gridWidth = width <= height ? width : height;
        const xStart = 0;
        const cellWidth = gridWidth / this.dimensions.width;
        const cellHeight = height / this.dimensions.height;

        for (let i = 0; i < this.dimensions.height; i++) {
            const y = i * cellHeight;
            for (let j = 0; j < this.dimensions.width; j++) {
                this.grid[i][j].rectangle.setSize(cellWidth - 2, cellHeight - 2);
                this.grid[i][j].rectangle.setPosition(j * cellWidth + xStart + 1, y + 1);
                this.grid[i][j].rectangle.setInteractive();
            }
        }
    }

    private hoverGrid(x: number, y: number): void {
        if (!this.grid[y][x].cell.isVisible) {
            this.grid[y][x].rectangle.input.cursor = 'pointer';
            this.grid[y][x].rectangle.fillAlpha = 0.7;
        }
    }

    private leaveGrid(x: number, y: number): void {
        if (!this.grid[y][x].cell.isVisible) {
            this.grid[y][x].rectangle.fillAlpha = 0.4;
        }
    }

    private clickGrid(x: number, y: number): void {
        if (x == this.clickPosition.x && y == this.clickPosition.y) {
            this.gameMaster.attack(this.grid[y][x].cell);
        }
    }

    private revealTile(cell: Cell): void {
        this.grid[cell.y][cell.x].rectangle.input.cursor = 'default';
        if (cell.boat) {
            this.grid[cell.y][cell.x].rectangle.fillColor = 0xFF0000;
        }
        this.tweens.add({
            targets: this.grid[cell.y][cell.x].rectangle,
            fillAlpha: 1,
            ease: 'Linear',
            duration: 1000,
            repeat: 0,
            yoyo: false
        });
    }
}

interface IGridElement {
    rectangle: GameObjects.Rectangle;
    cell: Cell;
}
