import React from "react";
import './card.css';
import { Link } from 'react-router-dom';

function Card(item){
    var data = item.data;
    return (
        <Link to={`/${item.service.id}/${data.id}`} className="card"  title={data.ru_title}>
            <div className="poster-container">
                <div className="blocks">
                    {data.announce &&
                        <div className="block" data-text="Анонс"></div>
                    }
                    {data.ongoing &&
                        <div className="block" data-text="Онгоинг"></div>
                    }
                    {data.info_blocks &&
                        data.info_blocks.map((block,key)=>{
                            return <div className="block" data-text={block} key={key}></div>
                        })
                    }
                </div>
                {data.series &&
                    <div className="series-info">{data.series}</div>
                }
                <img src={data.poster} alt={data.ru_title}></img>
            </div>
            <div className="title">{data.ru_title}</div>
        </Link>
    )
}

export default Card;