import React from 'react';
import services from '../../services';
import './index.css';
import { Link } from 'react-router-dom';
import Loading from '../../components/Loading/Loading';
class HomePage extends React.Component {
	
	constructor(props) {
		super(props);
		this.state = {
			error: null,
			isLoaded: false,
			items: {},
			shikimori: {},

		};
	}
	componentDidMount() {
		var data = {};
		Promise.all(services.map(id =>
			fetch(`http://127.0.0.1/api/${id.id}/`,{
				method: 'post',
				headers: {
					'Accept': 'application/json, text/plain, */*',
					'Content-Type': 'application/json'
				},
				body: JSON.stringify( {page: 1} ),
			}).then(resp => resp.json())
		))
		.then(responses => {
			console.log(responses);
		})
		.catch(error => {
				this.setState({
					isLoaded: false,
					error
				});
			});
		// Promise.all([
		// 	fetch('https://shikimori.one/api/topics?forum=news&limit=30'),
		// 	services.map(id => {
		// 		return fetch(`http://127.0.0.1/api/${id}/`)
		// 	})
		// ])
		// .then(async([...responces]) => {
		// 	console.log(responces);
		// 	// const a = await res1.json();
		// 	// const b = await res2.json();
		// 	// this.setState({
		// 	// 	isLoaded: false,
		// 	// 	error
		// 	// });

		// })
		// .catch(error => {
		// 	this.setState({
		// 		isLoaded: false,
		// 		error
		// 	});
		// });
		// fetch("https://shikimori.one/api/topics?forum=news&limit=30")
		// 	.then(res => res.json())
		// 	.then(
		// 		(result) => {
		// 			// data['shikimori'] = result
		// 			this.setState({
		// 				shikimori: result,
		// 			})
		// 		},
		// 		(error) => {
		// 			this.setState({
		// 				shikimori: error,
		// 			})
		// 		}
		// 	)
		// for (var service in services){
		// 	var id = services[service].id;
		// 	// alert(id);
		// 	fetch(`http://127.0.0.1/api/${id}/`,
		// 		{
		// 			method: 'post',
		// 			headers: {
		// 				'Accept': 'application/json, text/plain, */*',
		// 				'Content-Type': 'application/json'
		// 			},
		// 			body: JSON.stringify( {page: 1} ),
		// 		})
		// 		.then(res => res.json())
		// 		.then(
		// 			(result) => {
		// 				data[id] = result
		// 				console.log(data[id]);
		// 			},
		// 			(error) => {
		// 				console.log(error);
		// 				data[id] = error
		// 			}
		// 		)
		// }
		// console.log(data);
		// this.setState({
		// 	isLoaded: true,
		// 	items: data,
		// })

		// if (Object.keys(data).length !== 0){
		// 	this.setState({
		// 		isLoaded: true,
		// 		items: data,
		// 	})

		// } else {
		// 	this.setState({
		// 		isLoaded: false,
		// 		error: {
		// 			message: 'Сервер не вернул данные',
		// 		}
		// 	});
		// }
	}
	render() {
		const { error, isLoaded, items, shikimori } = this.state;
		console.log(items);
		console.log(shikimori);
		if (error) {
			return <div>Ошибка: {error.message}</div>;
		} else if (!isLoaded) {
			return <Loading/>;
		} else {
            return (
                <div className='wrapper'>
                    <div className='services'>
                        {services.map((el, index)=>{
                            return <Link className='service' key={index} to={"/"+el.id}>
                                <img src={el.icon}/>
                                <div className='title'>{el.title}</div>
                            </Link>
                        })}
                    </div>
                    <div className='cards w-100'>
                        {shikimori.map((el, index)=>{
                            return <a className='shikimori-card' key={index}>
                                {/* <div className='title'>{el.topic_title}</div> */}
								{function(){
									if (el.html_footer){
										var parser = new DOMParser();
										var footer = parser.parseFromString(el.html_footer, 'text/html');
										var images = [...footer.querySelectorAll('img')];
										if (images.length > 0){
											return <img src={images[0].attributes.src.nodeValue} />;
										}
										// [].forEach.call(footer.querySelectorAll('img'), (img, i)=>{
										// 	array.push(<img src={img.attributes.src.nodeValue} key={i}/>);
										// })
										// console.log();
										// return [];
									}
								}()}
                            </a>
                        })}
                    </div>
                </div>
            );
        }
    }
}
export default HomePage;
